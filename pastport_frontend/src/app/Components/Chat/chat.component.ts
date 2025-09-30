import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { MuseumChatWebSocketService, ChatResponse, ChatThinkingUpdate } from '../../Services/museum-chat-websocket.service';
import { AuthService } from '../../Services/auth.service';

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
export class ChatComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Component properties
  selectedArtifact: Artifact | null = null;
  chatMessages: ChatMessage[] = [];
  inputMessage = '';
  activeView: 'artifacts' | 'chat' | 'history' | 'photos' = 'artifacts';
  sidebarOpen = false;
  
  // WebSocket chat properties
  isConnected = false;
  isProcessing = false;
  currentSessionId = '';
  currentUserId = '';
  currentUserName = '';
  currentUserAgeGroup: 'child' | 'teen' | 'adult' | 'senior' = 'adult';
  currentThinkingMessage: ChatMessage | null = null;

  // Mock data - same as React version but updated for PastPort
  mockArtifacts: Artifact[] = [
    {
      id: 1,
      name: 'Rafflesia',
      period: 'Contemporary',
      location: 'Sumatra and Borneo',
      description: 'The genus includes the giant R. arnoldii, sometimes known as the corpse flower or monster flower, which produces the largest-known individual flower of any plant species in the world and is found in the forested mountains of Sumatra and Borneo. Its fully developed flower appears aboveground as a thick fleshy five-lobed structure weighing up to 11 kg (24 pounds) and measuring almost one meter (about one yard) across.',
      image: '/assets/images/rafflesia.jpg',
      category: 'Botany',
      dateDiscovered: 'Modern',
      significance: "World's largest flower",
    },
    {
      id: 2,
      name: 'American Rhinocerous Beetle',
      period: 'Contemporary',
      location: 'United States',
      description: 'The American rhinoceros beetle (Xyloryctes jamaicensis) is a species of scarab beetle native to the United States, characterized by the male\'s prominent head horn used for fighting, and a female that only has a small tubercle. These nocturnal, herbivorous beetles have larvae that live in the soil, feeding on decaying organic matter and sometimes roots, while the adults feed on tree cambium and sap.',
      image: '/assets/images/american_rhinocerous_beetle.png',
      category: 'Entomology',
      dateDiscovered: 'Modern',
      significance: 'Native beetle species',
    },
    {
      id: 3,
      name: 'Changi Tree Slice',
      period: 'Pre-1942',
      location: 'Changi, Singapore',
      description: 'The Sindora ×changiensis was a magnificent natural hybrid, endemic to Singapore, with a massive crown and distinctive velvety leaves. This centuries-old giant was so prominent it was marked on nautical charts for over 50 years as a pre-war landmark. In 1942, British forces tragically cut it down to prevent its use as a Japanese artillery marker. Carbon dating confirmed this heritage tree was at least 226 years old, making it one of the original inhabitants of the Changi rainforest.',
      image: '/assets/images/changi_tree_slice2.jpeg',
      category: 'Forestry Heritage',
      dateDiscovered: '1942',
      significance: 'Singapore heritage landmark',
    },
  ];

  mockChatHistory: ChatHistory[] = [
    {
      id: 1,
      artifactId: 1,
      artifactName: 'Rafflesia',
      lastMessage: 'How does the corpse flower attract pollinators?',
      timestamp: '2 hours ago',
    },
    {
      id: 2,
      artifactId: 2,
      artifactName: 'American Rhinocerous Beetle',
      lastMessage: 'What is the purpose of the male\'s horn?',
      timestamp: '1 day ago',
    },
  ];

  mockPhotoAlbum: PhotoAlbum[] = [
    {
      id: 1,
      image: '/assets/images/rafflesia.jpg',
      recognizedArtifacts: 1,
      timestamp: 'Today, 2:30 PM',
    },
    {
      id: 2,
      image: '/assets/images/changi_tree_slice2.jpeg',
      recognizedArtifacts: 1,
      timestamp: 'Yesterday, 4:15 PM',
    },
  ];

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private museumChatService: MuseumChatWebSocketService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.initializeChat();
    
    // Check if artifact ID is provided in route
    this.route.paramMap
      .pipe(takeUntil(this.destroy$))
      .subscribe(params => {
        const artifactId = params.get('artifactId');
        if (artifactId) {
          const artifact = this.mockArtifacts.find(a => a.id.toString() === artifactId);
          if (artifact) {
            this.handleArtifactSelect(artifact);
          }
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
    
    // Connect to chat service if not already connected
    if (!this.isConnected) {
      this.museumChatService.connect();
    }
  }

  handleHistoryItemClick(chat: ChatHistory): void {
    const artifact = this.mockArtifacts.find((a) => a.id === chat.artifactId);
    if (artifact) {
      this.selectedArtifact = artifact;
      this.activeView = 'chat';
      this.sidebarOpen = false;

      // Initialize with welcome back message
      this.chatMessages = [
        {
          id: "welcome_back",
          text: `Welcome back! Let's continue our discussion about the ${artifact.name}.`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
        }
      ];
    }
  }

  handlePhotoClick(photo: PhotoAlbum): void {
    this.sidebarOpen = false;
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

  // Helper methods
  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }

  setActiveView(view: 'artifacts' | 'chat' | 'history' | 'photos'): void {
    this.activeView = view;
  }

  // Navigation methods
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
