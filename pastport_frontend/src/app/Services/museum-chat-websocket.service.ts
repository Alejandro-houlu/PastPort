import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';

export interface ChatMessage {
  type: string;
  content: string;
  session_id: string;
  user_id: string;
  user_name?: string;
  user_age_group?: string;
  message_id?: string;
  image_result?: {
    label: string;
    confidence: number;
    entity_id: string;
  };
  timestamp?: number;
}

export interface ChatResponse {
  type: string; // "thinking", "response", "error", "status", "pong"
  content?: string;
  session_id: string;
  message_id?: string;
  stage?: string; // For thinking updates
  source?: string; // Response source (museum_rag, openai_web, etc.)
  contexts?: Array<{
    content: string;
    metadata: any;
    relevance_score: number;
    id: string;
  }>;
  metadata?: any;
}

export interface ChatThinkingUpdate {
  stage: string;
  content: string;
}

@Injectable({
  providedIn: 'root'
})
export class MuseumChatWebSocketService {
  private socket: WebSocket | null = null;
  private readonly wsUrl = `${environment.wsUrl}/ws/chat`;
  
  // Subjects for different message types
  private connectionStatus$ = new BehaviorSubject<boolean>(false);
  private chatResponses$ = new Subject<ChatResponse>();
  private thinkingUpdates$ = new Subject<ChatThinkingUpdate>();
  private errors$ = new Subject<string>();
  private recommendations$ = new Subject<any>();
  private headerUpdates$ = new Subject<any>();
  
  // Connection management
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  
  // Current user context
  private currentUserId: string = '';
  private currentUserName: string = '';
  private currentUserAgeGroup: string = 'adult';

  constructor() {}

  /**
   * Initialize the service with user context
   */
  initialize(userId: string, userAgeGroup: string = 'adult', userName: string = ''): void {
    this.currentUserId = userId;
    this.currentUserAgeGroup = userAgeGroup;
    this.currentUserName = userName;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    console.log('🔌 Attempting to connect to Museum Chat WebSocket:', this.wsUrl);
    
    // Disconnect existing connection if any
    if (this.socket) {
      console.log('🔄 Closing existing WebSocket connection');
      this.disconnect();
    }
    
    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.wsUrl);
        
        this.socket.onopen = () => {
          console.log('✅ Museum Chat WebSocket connected successfully');
          this.connectionStatus$.next(true);
          this.reconnectAttempts = 0;
          resolve();
        };
        
        this.socket.onmessage = (event) => {
          this.handleMessage(event.data);
        };
        
        this.socket.onclose = (event) => {
          console.log('🔌 Museum Chat WebSocket disconnected:', event.code, event.reason);
          this.connectionStatus$.next(false);
          this.socket = null;
          
          // Attempt reconnection if not manually closed
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect();
          }
        };
        
        this.socket.onerror = (error) => {
          console.error('💥 Museum Chat WebSocket error:', error);
          this.errors$.next('WebSocket connection error');
          reject(error);
        };
        
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      console.log('🔌 Disconnecting Museum Chat WebSocket...');
      this.socket.close(1000, 'Manual disconnect');
      this.socket = null;
      this.connectionStatus$.next(false);
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.connect().catch(() => {
          // Connection failed, will trigger another reconnect attempt
        });
      }
    }, delay);
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection status observable
   */
  getConnectionStatus(): Observable<boolean> {
    return this.connectionStatus$.asObservable();
  }

  /**
   * Get chat responses observable
   */
  getChatResponses(): Observable<ChatResponse> {
    return this.chatResponses$.asObservable();
  }

  /**
   * Get thinking updates observable
   */
  getThinkingUpdates(): Observable<ChatThinkingUpdate> {
    return this.thinkingUpdates$.asObservable();
  }

  /**
   * Get errors observable
   */
  getErrors(): Observable<string> {
    return this.errors$.asObservable();
  }

  /**
   * Get recommendations observable
   */
  getRecommendations(): Observable<any> {
    return this.recommendations$.asObservable();
  }

  /**
   * Get header updates observable
   */
  getHeaderUpdates(): Observable<any> {
    return this.headerUpdates$.asObservable();
  }

  /**
   * Send a chat message
   */
  sendMessage(
    content: string,
    sessionId: string,
    imageResult?: { label: string; confidence: number; entity_id: string },
    messageId?: string
  ): void {
    if (!this.isConnected()) {
      console.warn('WebSocket not connected, cannot send message');
      this.errors$.next('Not connected to chat service');
      return;
    }
    const finalMessageId = messageId ?? this.generateMessageId();

    const message: ChatMessage = {
      type: 'query',
      content: content,
      session_id: sessionId,
      user_id: this.currentUserId,
      user_name: this.currentUserName,
      user_age_group: this.currentUserAgeGroup,
      message_id: finalMessageId,
      image_result: imageResult,
      timestamp: Date.now()
    };

    console.log('📤 Sending chat message:', { content: content.substring(0, 50), sessionId, finalMessageId });
    this.sendRawMessage(message);
  }

  /**
   * Send ping to server
   */
  sendPing(sessionId: string): void {
    if (!this.isConnected()) {
      return;
    }

    const message: ChatMessage = {
      type: 'ping',
      content: 'ping',
      session_id: sessionId,
      user_id: this.currentUserId,
      timestamp: Date.now()
    };

    this.sendRawMessage(message);
  }

  /**
   * Request system status
   */
  requestStatus(sessionId: string): void {
    if (!this.isConnected()) {
      return;
    }

    const message: ChatMessage = {
      type: 'status',
      content: 'status',
      session_id: sessionId,
      user_id: this.currentUserId,
      timestamp: Date.now()
    };

    this.sendRawMessage(message);
  }

  /**
   * Update user context (age group, etc.)
   */
  updateUserContext(userId?: string, userAgeGroup?: string): void {
    if (userId) this.currentUserId = userId;
    if (userAgeGroup) this.currentUserAgeGroup = userAgeGroup;
    
    console.log('👤 Updated user context:', { userId: this.currentUserId, ageGroup: this.currentUserAgeGroup });
  }

  /**
   * Generate a unique message ID
   */
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Send raw message to WebSocket server
   */
  private sendRawMessage(message: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      try {
        this.socket.send(JSON.stringify(message));
      } catch (error) {
        console.error('💥 Error sending WebSocket message:', error);
        this.errors$.next('Failed to send message to server');
      }
    } else {
      console.warn('⚠️ Cannot send message - WebSocket not connected');
      this.errors$.next('Connection lost - attempting to reconnect');
      
      // Try to reconnect
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.attemptReconnect();
      }
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: string): void {
    try {
      const response: ChatResponse = JSON.parse(data);
      console.log('📨 Received WebSocket message:', response.type);
      
      switch (response.type) {
        case 'thinking':
          // Handle thinking/processing updates
          if (response.stage && response.content) {
            this.thinkingUpdates$.next({
              stage: response.stage,
              content: response.content
            });
          }
          break;
          
        case 'response':
          // Handle final chat responses
          console.log(`💬 Chat response received (source: ${response.source})`);
          this.chatResponses$.next(response);
          break;
          
        case 'error':
          // Handle errors
          const errorMsg = response.content || 'Unknown chat error';
          console.error('❌ Chat error:', errorMsg);
          this.errors$.next(errorMsg);
          break;
          
        case 'status':
          // Handle status responses
          console.log('📊 Status response:', response.metadata);
          this.chatResponses$.next(response);
          break;
          
        case 'pong':
          // Handle pong responses
          console.log('🏓 Received pong from server');
          break;
        
        case 'recommendations':
          // Handle question recommendations
          console.log('💡 Question recommendations received');
          if (response.metadata && response.metadata.recommendations) {
            this.recommendations$.next(response.metadata.recommendations);
          }
          break;
        
        case 'header_update':
          // Handle artifact header updates
          console.log('🖼️ Artifact header update received');
          if (response.metadata && response.metadata.artifact_data) {
            this.headerUpdates$.next(response.metadata.artifact_data);
          }
          break;
          
        default:
          console.warn('❓ Unknown message type:', response.type);
      }
      
    } catch (error) {
      console.error('💥 Failed to parse WebSocket message:', error);
      this.errors$.next('Failed to parse server message');
    }
  }

  /**
   * Get current user context
   */
  getCurrentUserContext(): { userId: string; userAgeGroup: string } {
    return {
      userId: this.currentUserId,
      userAgeGroup: this.currentUserAgeGroup
    };
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    console.log('🧹 Cleaning up Museum Chat WebSocket service');
    this.disconnect();
    
    // Complete all subjects
    this.connectionStatus$.complete();
    this.chatResponses$.complete();
    this.thinkingUpdates$.complete();
    this.errors$.complete();
  }
}
