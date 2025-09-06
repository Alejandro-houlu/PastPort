import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { RouterModule } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';

// Mock data interfaces - same as React version
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
  id: number;
  text: string;
  isUser: boolean;
  timestamp: string;
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
  
  // Component properties - equivalent to React useState
  selectedArtifact: Artifact | null = null;
  chatMessages: ChatMessage[] = [];
  inputMessage = '';
  activeView: 'artifacts' | 'chat' | 'history' | 'photos' = 'artifacts';
  sidebarOpen = false;

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
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
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
    this.destroy$.next();
    this.destroy$.complete();
  }

  // Component methods - equivalent to React functions
  handleArtifactSelect(artifact: Artifact): void {
    this.selectedArtifact = artifact;
    this.activeView = 'chat';
    this.sidebarOpen = false; // Auto-close sidebar

    // Initialize chat with welcome message
    this.chatMessages = [
      {
        id: 1,
        text: `Hello! I'm your AI museum guide. I can tell you more about the ${artifact.name}. What would you like to know?`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
      },
    ];
  }

  handleHistoryItemClick(chat: ChatHistory): void {
    // Find the artifact associated with this chat
    const artifact = this.mockArtifacts.find((a) => a.id === chat.artifactId);
    if (artifact) {
      this.selectedArtifact = artifact;
      this.activeView = 'chat';
      // Auto-close sidebar when viewing full chat history in main area
      this.sidebarOpen = false;

      // Load previous chat messages (mock implementation)
      this.chatMessages = [
        {
          id: 1,
          text: `Welcome back! Let's continue our discussion about the ${artifact.name}.`,
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
        },
        {
          id: 2,
          text: chat.lastMessage,
          isUser: true,
          timestamp: chat.timestamp,
        },
      ];
    }
  }

  handlePhotoClick(photo: PhotoAlbum): void {
    // Auto-close sidebar when viewing full photo details in main area
    this.sidebarOpen = false;
    // Could expand to show photo analysis in main area
  }

  handleSendMessage(): void {
    if (!this.inputMessage.trim() || !this.selectedArtifact) return;

    const userMessage: ChatMessage = {
      id: this.chatMessages.length + 1,
      text: this.inputMessage,
      isUser: true,
      timestamp: new Date().toLocaleTimeString(),
    };

    // Mock AI response
    const aiResponse: ChatMessage = {
      id: this.chatMessages.length + 2,
      text: `That's a great question about the ${this.selectedArtifact.name}! This artifact from the ${this.selectedArtifact.period} is particularly interesting because of its ${this.selectedArtifact.significance}. The piece was discovered in ${this.selectedArtifact.dateDiscovered} and represents the artistic traditions of ${this.selectedArtifact.category}.`,
      isUser: false,
      timestamp: new Date().toLocaleTimeString(),
    };

    this.chatMessages = [...this.chatMessages, userMessage, aiResponse];
    this.inputMessage = '';
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
