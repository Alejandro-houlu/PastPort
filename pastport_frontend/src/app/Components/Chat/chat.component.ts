import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { MuseumChatWebSocketService, ChatResponse, ChatThinkingUpdate } from '../../Services/museum-chat-websocket.service';
import { AuthService } from '../../Services/auth.service';
import { UserClickHistoryService, ArtifactClick, ChatHistoryItem } from '../../Services/user-click-history.service';
import { QuestionRecommenderService, QuestionRecommendations } from '../../Services/question-recommender.service';

// Interfaces for chat functionality
interface Artifact {
  id: number;
  name: string;
  period: string;
  location: string;
  description: string;
  image: string;
  category: string;
  dateDiscovered: string;
  significance: string;
}

interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
  source?: string; // museum_rag, openai_web, etc.
  contexts?: Array<{
    content: string;
    metadata: any;
    relevance_score: number;
    id: string;
  }>;
  isThinking?: boolean;
  thinkingStage?: string;
}

interface ChatHistory {
  id: number;
  artifactId: number;
  artifactName: string;
  lastMessage: string;
  timestamp: string;
}

interface PhotoAlbum {
  id: number;
  image: string;
  recognizedArtifacts: number;
  timestamp: string;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule
  ],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  private destroy$ = new Subject<void>();
  
  // ViewChild for auto-scrolling
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  private shouldScrollToBottom = false;
  
  // Component properties
  selectedArtifact: Artifact | null = null;
  showArtifactHeader = false;
  chatMessages: ChatMessage[] = [];
  inputMessage = '';
  activeView: 'artifacts' | 'chat' | 'history' | 'photos' = 'artifacts';
  sidebarOpen = false;
  referrerRoute: string = '/dashboard'; // Default to dashboard
  
  // WebSocket chat properties
  isConnected = false;
  isProcessing = false;
  currentSessionId = '';
  currentUserId = '';
  currentUserName = '';
  currentUserAgeGroup: 'child' | 'teen' | 'adult' | 'senior' = 'adult';
  currentThinkingMessage: ChatMessage | null = null;

  // Real data from backend
  recentArtifacts: ArtifactClick[] = [];
  chatHistory: ChatHistoryItem[] = [];
  isLoadingArtifacts = false;
  isLoadingHistory = false;

  // Question recommender properties
  recommendedQuestions: QuestionRecommendations | null = null;
  showRecommendations = false;
  isLoadingRecommendations = false;
  
  // Mobile responsiveness
  isMobileView = false;
  hasStartedChatOnMobile = false;

  mockPhotoAlbum: PhotoAlbum[] = []; // Keep for future photo album feature

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private museumChatService: MuseumChatWebSocketService,
    private authService: AuthService,
    private clickHistoryService: UserClickHistoryService,
    private questionRecommenderService: QuestionRecommenderService
  ) {}

  ngOnInit(): void {
    this.initializeChat();
    
    // Check if mobile view
    this.checkMobileView();
    
    // Listen for window resize
    if (typeof window !== 'undefined') {
      window.addEventListener('resize', () => this.checkMobileView());
    }
    
    // Capture referrer route from query params or navigation state
    this.route.queryParams
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        if (params['from']) {
          this.referrerRoute = params['from'];
        }
      });
    
    // Load recent clicks and chat history
    this.loadRecentArtifacts();
    this.loadChatHistory();
    
    // Check if artifact ID is provided in route
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        const artifactId = params.get('artifactId');
        if (artifactId) {
          // Arrived from artifact page - show artifact header
          this.showArtifactHeader = true;
          // Set referrer to artifact page if not already set
          if (this.referrerRoute === '/dashboard') {
            this.referrerRoute = `/artifact/${artifactId}`;
          }
          // Find artifact in recent clicks
          const artifact = this.recentArtifacts.find(a => a.id === artifactId);
          if (artifact) {
            this.handleArtifactClick(artifact);
          }
        } else {
          // Arrived from sidebar - no artifact context
          this.showArtifactHeader = false;
          // Keep activeView as 'artifacts' (default)
        }
      });
  }

  ngOnDestroy(): void {
    this.museumChatService.disconnect();
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initializeChat(): void {
    // Get current user from auth service
    const currentUser = this.authService.getCurrentUser();
    
    if (currentUser) {
      this.currentUserId = currentUser.id;
      this.currentUserName = currentUser.name;
      this.currentUserAgeGroup = currentUser.age_group;
      console.log(`Initialized chat for user: ${currentUser.name} (${currentUser.id}), age group: ${currentUser.age_group}`);
    } else {
      console.warn('No authenticated user found, chat may not work properly');
      // Redirect to login if no user is authenticated
      this.router.navigate(['/login']);
      return;
    }

    // Initialize WebSocket service with user context
    this.museumChatService.initialize(this.currentUserId, this.currentUserAgeGroup, this.currentUserName);
    
    // Generate session ID
    this.currentSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Subscribe to connection status
    this.museumChatService.getConnectionStatus()
      .pipe(takeUntil(this.destroy$))
      .subscribe(connected => {
        this.isConnected = connected;
        console.log('Museum chat connection status:', connected);
      });
    
    // Subscribe to chat responses
    this.museumChatService.getChatResponses()
      .pipe(takeUntil(this.destroy$))
      .subscribe(response => {
        this.handleChatResponse(response);
      });
    
    // Subscribe to thinking updates
    this.museumChatService.getThinkingUpdates()
      .pipe(takeUntil(this.destroy$))
      .subscribe(update => {
        this.handleThinkingUpdate(update);
      });
    
    // Subscribe to errors
    this.museumChatService.getErrors()
      .pipe(takeUntil(this.destroy$))
      .subscribe(error => {
        this.handleChatError(error);
      });
    
    // Subscribe to recommendations
    this.museumChatService.getRecommendations()
      .pipe(takeUntil(this.destroy$))
      .subscribe(recommendations => {
        this.handleRecommendations(recommendations);
      });
    
    // Subscribe to header updates
    this.museumChatService.getHeaderUpdates()
      .pipe(takeUntil(this.destroy$))
      .subscribe(artifactData => {
        this.handleHeaderUpdate(artifactData);
      });
    
    // Connect to WebSocket
    this.museumChatService.connect().catch(error => {
      console.error('Failed to connect to museum chat:', error);
    });
  }

  private handleChatResponse(response: ChatResponse): void {
    this.isProcessing = false;
    
    // Remove thinking message if exists
    if (this.currentThinkingMessage) {
      this.chatMessages = this.chatMessages.filter(msg => msg.id !== this.currentThinkingMessage!.id);
      this.currentThinkingMessage = null;
    }
    
    // Add the actual response
    const aiMessage: ChatMessage = {
      id: response.message_id || `msg_${Date.now()}`,
      text: response.content || 'I apologize, I could not generate a response.',
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      source: response.source,
      contexts: response.contexts
    };
    
    this.chatMessages = [...this.chatMessages, aiMessage];
    this.shouldScrollToBottom = true; // Trigger scroll after AI response
  }

  private handleThinkingUpdate(update: ChatThinkingUpdate): void {
    // Update or create thinking message
    if (this.currentThinkingMessage) {
      // Update existing thinking message
      this.currentThinkingMessage.text = update.content;
      this.currentThinkingMessage.thinkingStage = update.stage;
    } else {
      // Create new thinking message
      this.currentThinkingMessage = {
        id: `thinking_${Date.now()}`,
        text: update.content,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        isThinking: true,
        thinkingStage: update.stage
      };
      this.chatMessages = [...this.chatMessages, this.currentThinkingMessage];
    }
    this.shouldScrollToBottom = true; // Scroll to bottom on every thinking update
  }

  private handleChatError(error: string): void {
    this.isProcessing = false;
    
    // Remove thinking message if exists
    if (this.currentThinkingMessage) {
      this.chatMessages = this.chatMessages.filter(msg => msg.id !== this.currentThinkingMessage!.id);
      this.currentThinkingMessage = null;
    }
    
    // Add error message
    const errorMessage: ChatMessage = {
      id: `error_${Date.now()}`,
      text: `Sorry, I encountered an error: ${error}`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
      source: 'error'
    };
    
    this.chatMessages = [...this.chatMessages, errorMessage];
  }

  handleArtifactSelect(artifact: Artifact): void {
    this.selectedArtifact = artifact;
    this.activeView = 'chat';
    this.sidebarOpen = false;

    // Initialize chat with welcome message
    this.chatMessages = [
      {
        id: "welcome",
        text: `Hello! I'm your AI museum guide. I can tell you more about the ${artifact.name}. What would you like to know?`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
      },
    ];
    
    // Note: WebSocket connection is already established in initializeChat()
    // No need to connect again here
  }

  /**
   * Load recent artifact clicks from backend
   */
  private loadRecentArtifacts(): void {
    if (!this.currentUserId) return;
    
    this.isLoadingArtifacts = true;
    this.clickHistoryService.getRecentClicks(this.currentUserId, 5)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (artifacts) => {
          this.recentArtifacts = artifacts;
          console.log('Loaded recent artifacts:', artifacts);
          this.isLoadingArtifacts = false;
        },
        error: (error) => {
          console.error('Error loading recent artifacts:', error);
          this.isLoadingArtifacts = false;
        }
      });
  }

  /**
   * Load chat history from backend
   */
  private loadChatHistory(): void {
    if (!this.currentUserId) return;
    
    this.isLoadingHistory = true;
    this.clickHistoryService.getChatHistory(this.currentUserId, 10)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (history) => {
          this.chatHistory = history;
          console.log('Loaded chat history:', history);
          this.isLoadingHistory = false;
        },
        error: (error) => {
          console.error('Error loading chat history:', error);
          this.isLoadingHistory = false;
        }
      });
  }

  /**
   * Handle artifact click from the sidebar - starts FRESH conversation
   */
  handleArtifactClick(artifactClick: ArtifactClick): void {
    // Show artifact header when clicking from sidebar
    this.showArtifactHeader = true;
    
    // Convert ArtifactClick to Artifact interface
    const artifact: Artifact = {
      id: 0,
      name: artifactClick.artifact_name,
      period: 'Contemporary',
      location: artifactClick.museum_location || 'Unknown',
      description: artifactClick.description || '',
      image: artifactClick.image_url || '/assets/images/rafflesia.jpg',
      category: 'Artifact',
      dateDiscovered: 'Modern',
      significance: ''
    };
    
    // Use handleArtifactSelect to show welcome message and start fresh
    this.handleArtifactSelect(artifact);
    
    // Load question recommendations for this artifact
    this.loadQuestionRecommendations(artifactClick.artifact_name);
  }

  /**
   * Load question recommendations from backend
   */
  private loadQuestionRecommendations(artifactName: string): void {
    this.isLoadingRecommendations = true;
    
    this.questionRecommenderService.getRecommendations(artifactName)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (recommendations) => {
          if (recommendations.success) {
            this.recommendedQuestions = recommendations;
            this.showRecommendations = true;
            console.log('Loaded question recommendations:', recommendations);
          } else {
            console.log('No recommendations available for', artifactName);
            this.recommendedQuestions = null;
            this.showRecommendations = false;
          }
          this.isLoadingRecommendations = false;
        },
        error: (error) => {
          console.error('Error loading question recommendations:', error);
          this.recommendedQuestions = null;
          this.showRecommendations = false;
          this.isLoadingRecommendations = false;
        }
      });
  }

  /**
   * Handle clicking on a recommended question
   */
  handleRecommendedQuestionClick(question: string): void {
    // Set the input message and send immediately
    this.inputMessage = question;
    this.handleSendMessage();
  }

  /**
   * Handle incoming recommendations from WebSocket
   */
  private handleRecommendations(recommendations: any): void {
    if (recommendations && recommendations.success) {
      this.recommendedQuestions = recommendations;
      this.showRecommendations = true;
      console.log('Received dynamic question recommendations:', recommendations);
      this.shouldScrollToBottom = true; // Scroll to bottom when recommendations appear
    } else {
      console.log('No recommendations in WebSocket message');
    }
  }

  /**
   * Handle incoming artifact header updates from WebSocket
   */
  private handleHeaderUpdate(artifactData: any): void {
    if (artifactData.is_general_question) {
      // General question - hide artifact header
      console.log('General question detected - hiding artifact header');
      this.showArtifactHeader = false;
      this.selectedArtifact = null;
    } else if (artifactData) {
      // Update to new artifact
      console.log('Updating artifact header to:', artifactData.artifact_name);
      this.selectedArtifact = {
        id: artifactData.id || 0,
        name: artifactData.artifact_name || 'Unknown',
        period: 'Contemporary',
        location: artifactData.museum_location || 'Unknown',
        description: artifactData.description || '',
        image: artifactData.image_url || '/assets/images/rafflesia.jpg',
        category: artifactData.category || 'Artifact',
        dateDiscovered: artifactData.display_startDate || 'Modern',
        significance: artifactData.significance || ''
      };
      this.showArtifactHeader = true;
    }
  }

  /**
   * Dismiss the recommendations panel
   */
  dismissRecommendations(): void {
    this.showRecommendations = false;
  }

  /**
   * Handle chat history item click - loads EXISTING conversation
   */
  handleChatHistoryClick(historyItem: ChatHistoryItem): void {
    this.activeView = 'chat';
    this.sidebarOpen = false;
    this.selectedArtifact = null; // No specific artifact for history
    
    // Load the existing messages from this session
    this.clickHistoryService.getSessionMessages(historyItem.session_id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (sessionData) => {
          console.log('Loaded session messages:', sessionData);
          
          // Convert session messages to chat messages
          this.chatMessages = sessionData.messages.map((msg: any) => ({
            id: msg.message_id,
            text: msg.user_query,
            isUser: true,
            timestamp: new Date(msg.timestamp).toLocaleTimeString()
          })).concat(sessionData.messages.map((msg: any) => ({
            id: `ai_${msg.message_id}`,
            text: msg.museum_response,
            isUser: false,
            timestamp: new Date(msg.timestamp).toLocaleTimeString(),
            source: msg.source,
            contexts: msg.contexts
          }))).sort((a: ChatMessage, b: ChatMessage) => {
            // Sort by timestamp to maintain conversation order
            return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
          });
          
          // Update session ID to continue this conversation
          this.currentSessionId = historyItem.session_id;
        },
        error: (error) => {
          console.error('Error loading session messages:', error);
          this.chatMessages = [{
            id: 'error',
            text: 'Failed to load chat history. Please try again.',
            isUser: false,
            timestamp: new Date().toLocaleTimeString(),
            source: 'error'
          }];
        }
      });
  }

  handlePhotoClick(photo: PhotoAlbum): void {
    this.sidebarOpen = false;
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  private scrollToBottom(): void {
    try {
      if (this.messagesContainer) {
        this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
      }
    } catch (err) {
      console.error('Could not scroll to bottom:', err);
    }
  }

  handleSendMessage(): void {
    if (!this.inputMessage.trim() || !this.isConnected || this.isProcessing) {
      return;
    }

    const messageText = this.inputMessage.trim();
    this.inputMessage = ''; // Clear input immediately
    this.isProcessing = true;

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      text: messageText,
      isUser: true,
      timestamp: new Date().toLocaleTimeString(),
    };
    
    this.chatMessages = [...this.chatMessages, userMessage];
    this.shouldScrollToBottom = true; // Trigger scroll after message added

    // On mobile, auto-hide recommendations after first query is sent
    if (this.isMobileView && !this.hasStartedChatOnMobile) {
      this.hasStartedChatOnMobile = true;
      this.showRecommendations = false;
      console.log('Mobile: Auto-hiding recommendations after first query');
    }

    // Prepare image result if available (from camera recognition)
    const imageResult = this.selectedArtifact ? {
      label: this.selectedArtifact.name,
      confidence: 0.95,
      entity_id: this.selectedArtifact.id.toString()
    } : undefined;

    // Send message through WebSocket service
    this.museumChatService.sendMessage(
      messageText,
      this.currentSessionId,
      imageResult
    );
  }

  /**
   * Check if current viewport is mobile
   */
  private checkMobileView(): void {
    if (typeof window !== 'undefined') {
      this.isMobileView = window.innerWidth <= 576;
      console.log('Mobile view:', this.isMobileView);
    }
  }

  /**
   * Get mobile-optimized recommendations (max 2 questions)
   * Prioritizes: same_intent_species and diff_species_same_intent
   */
  getMobileRecommendations(): { same_species: string[], diff_species: string[] } {
    if (!this.recommendedQuestions) {
      return { same_species: [], diff_species: [] };
    }

    const sameSpecies = this.recommendedQuestions.questions.same_intent_species || [];
    const diffSpecies = this.recommendedQuestions.questions.diff_species_same_intent || [];
    
    // If total is 2 or less, return all
    const totalQuestions = sameSpecies.length + diffSpecies.length;
    if (totalQuestions <= 2) {
      return { same_species: sameSpecies, diff_species: diffSpecies };
    }
    
    // Otherwise, limit to max 2 total, prioritizing same_species first
    const result: { same_species: string[], diff_species: string[] } = { same_species: [], diff_species: [] };
    let remaining = 2;
    
    // First, add from same_species (up to 2)
    const sameToAdd = Math.min(sameSpecies.length, remaining);
    result.same_species = sameSpecies.slice(0, sameToAdd);
    remaining -= sameToAdd;
    
    // Then add from diff_species if we still have slots
    if (remaining > 0) {
      result.diff_species = diffSpecies.slice(0, remaining);
    }
    
    return result;
  }

  // Helper methods
  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }

  setActiveView(view: 'artifacts' | 'chat' | 'history' | 'photos'): void {
    this.activeView = view;
  }

  // Navigation methods
  goBack(): void {
    this.router.navigate([this.referrerRoute]);
  }

  goBackToCamera(): void {
    this.router.navigate(['/camera']);
  }

  goBackToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  // Handle keyboard events
  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      this.handleSendMessage();
    }
  }
}
