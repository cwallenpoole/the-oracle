# The Oracle - AI-Powered Divination Platform

> **A mystical journey into the future, guided by ancient wisdom and modern AI**

The Oracle is a sophisticated Flask-based web application that combines traditional divination practices with cutting-edge artificial intelligence. This project represents a unique collaboration between human creativity and AI assistance, with **over 90% of the codebase developed through human direction of Cursor.ai** - demonstrating the power of human-AI partnership in software development.

## 🌟 Key Highlights

- **Human-AI Collaboration**: Over 90% of this application was created through human developers directing Cursor.ai, showcasing the future of software development
- **Multi-Modal Divination**: Supports I Ching (Book of Changes) and Elder Futhark Runes with multiple spread types and a form of Pyromancy
- **Advanced AI Integration**: Features OpenAI GPT-4, Ollama local models, and DALL-E 3 for text and image generation
- **Vector Database**: Uses VectorDB to provide the AI additional context and memory for enhanced readings
- **Advanced Pyromancy**: Interactive fire canvas with mystical flame generation and image capture
- **Comprehensive Testing**: Full test suite with performance monitoring and coverage analysis

## 📸 Screenshots

### Main Dashboard - Divination Selection
![Main Dashboard](docs/screenshots/main-dashboard.png)
*The Oracle's main interface showing divination method selection, user profile, and recent reading history*

### Interactive Pyromancy Experience
![Pyromancy Interface](docs/screenshots/pyromancy-interface.png)
*Interactive fire canvas with mystical flame generation, color selection, and image capture capabilities*

### I Ching Reading Results
![I Ching Reading](docs/screenshots/iching-reading.png)
*Complete I Ching reading showing hexagram casting, AI interpretation, and detailed analysis*

### Runic Reading with Multiple Spreads
![Runic Reading](docs/screenshots/runic-reading.png)
*Elder Futhark rune reading with spread visualization and AI-powered interpretation*



## 🔮 Divination Systems

### I Ching (Book of Changes)
- **64 Hexagrams**: Complete traditional hexagram system with authentic interpretations
- **Dynamic Casting**: Real-time hexagram generation using traditional coin or yarrow stalk methods
- **AI-Enhanced Readings**: Personalized interpretations using OpenAI GPT-4 or local Ollama models
- **Historical Context**: Rich database of traditional I Ching texts and meanings

### Elder Futhark Runes
- **24 Traditional Runes**: Complete set of ancient Norse runes with authentic meanings
- **Multiple Spreads**:
  - **Single Rune**: Quick guidance and insight
  - **Three Norns**: Past, Present, Future reading
  - **Five Rune Cross**: Comprehensive life guidance
  - **Seven Chakras**: Energy center alignment reading
- **AI-Powered Interpretation**: Contextual readings based on question and spread type

## 🤖 AI & Machine Learning Features

### Multi-Provider LLM Support
- **OpenAI Integration**: GPT-4 for high-quality text generation
- **Ollama Local Models**: Support for local LLM deployment (Llama 3.2, etc.)
- **Intelligent Fallback**: Automatic switching between providers for reliability
- **Custom Prompts**: Specialized system prompts for each divination type


### Vector Database & Memory
- **Local Vector Storage**: `vectordb2` for offline memory management
- **Chunking Strategy**: Sliding window approach for optimal text processing
- **Semantic Search**: Find relevant hexagrams based on natural language queries

## 🏗️ Technical Architecture

### Backend Framework
- **Flask**: Lightweight, flexible web framework
- **SQLite**: Embedded database for user data and reading history
- **SQLAlchemy**: ORM for database operations
- **Blueprint Architecture**: Modular route organization

### Frontend Technologies
- **Bootstrap 5**: Responsive, modern UI framework
- **JavaScript**: Dynamic interactions and AJAX requests
- **HTML5/CSS3**: Semantic markup and custom styling
- **Jinja2 Templates**: Server-side templating engine

### AI & ML Stack
- **OpenAI API**: GPT-4 and DALL-E 3 integration
- **Ollama**: Local LLM deployment and management
- **Pinecone**: Vector database for semantic search
- **LangChain**: LLM orchestration and prompt management
- **Sentence Transformers**: Text embedding generation

## 📁 Project Structure

```
the-oracle/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── logic/                # Core divination logic
│   ├── iching.py         # I Ching implementation
│   ├── runes.py          # Runic system implementation
│   ├── ai_readers.py     # AI-powered reading generation
│   └── base.py           # Abstract divination framework
├── routes/               # Flask route blueprints
│   ├── auth.py           # User authentication
│   ├── readings.py       # Divination reading endpoints
│   └── api.py            # API endpoints
├── models/               # Database models
│   ├── user.py           # User management
│   ├── history.py        # Reading history
│   └── llm_request.py    # LLM request tracking
├── utils/                # Utility functions
│   ├── db_utils.py       # Database operations
│   ├── hexagram_utils.py # I Ching utilities
│   └── wiki_utils.py     # Wikipedia integration
├── llm/                  # AI/ML components
│   ├── memory.py         # Vector memory system
│   └── pinecode.py       # Pinecone integration
├── templates/            # HTML templates
├── static/               # Static assets
└── tests/                # Test suite
```

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Virtual environment (included: `the-oracle/`)
- OpenAI API key (optional, for AI features)
- Pinecone API key (optional, for vector search)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd the-oracle
   ```

2. **Activate virtual environment**
   ```bash
   source the-oracle/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Initialize database**
   ```bash
   python -c "from utils.db_utils import init_db; init_db()"
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser to `http://localhost:7878`

## 🧪 Testing & Quality Assurance

### Comprehensive Test Suite
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end functionality testing
- **Performance Tests**: Response time and memory usage monitoring
- **Coverage Analysis**: Code coverage reporting

### Running Tests
```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run performance profiling
python run_tests.py --profile
```

### Performance Monitoring
```bash
# Real-time monitoring
python performance_monitor.py monitor 5

# Performance profiling
python performance_monitor.py profile 100
```

## 🔧 Development Tools

### Reading Management
- **List Readings**: `python list_readings.py` - View all available readings
- **Regenerate Readings**: `python regenerate_reading.py <id>` - Update AI interpretations
- **Reading History**: Complete audit trail of all divination sessions

### AI Model Management
- **Ollama Integration**: Local model deployment and management
- **Model Switching**: Seamless switching between OpenAI and Ollama
- **Request Tracking**: Complete logging of all LLM interactions

## 🌐 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User authentication
- `POST /logout` - User logout

### Divination
- `POST /readings` - Create new reading
- `GET /readings/<path>` - View reading details
- `GET /api/hexagrams` - List all hexagrams
- `GET /api/runes` - List all runes

### AI Features
- `POST /api/generate-vision-images` - Generate vision images
- `GET /api/vision-images-status/<id>` - Check generation status
- `POST /api/regenerate-reading` - Regenerate AI interpretation

## 🎨 User Interface

### Modern Design
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Bootstrap 5**: Professional, accessible UI components
- **Custom Styling**: Mystical theme with fire and rune aesthetics
- **Interactive Elements**: Dynamic forms and real-time updates

### User Experience
- **Intuitive Navigation**: Clear, logical flow through divination process
- **Reading History**: Easy access to past readings
- **Profile Management**: User preferences and settings
- **Visual Feedback**: Loading states and progress indicators

## 🔮 Divination Features

### I Ching System
- **Traditional Casting**: Coin and yarrow stalk methods
- **Hexagram Database**: Complete 64 hexagram interpretations
- **Changing Lines**: Dynamic hexagram transformations
- **AI Interpretation**: Personalized readings based on question context

### Runic System
- **Elder Futhark**: Complete 24-rune system
- **Multiple Spreads**: Single, Three Norns, Five Cross, Seven Chakras
- **Rune Meanings**: Traditional and modern interpretations
- **Spread Visualization**: Visual representation of rune positions

## 🤝 Human-AI Collaboration

This project exemplifies the future of software development, where human creativity and AI capabilities combine to create something greater than either could achieve alone. The development process involved:

### Development Approach
- **Human Direction**: All features, architecture, and design decisions made by human developers
- **AI Assistance**: Cursor.ai provided code generation, refactoring, and implementation support
- **Collaborative Iteration**: Continuous refinement through human-AI dialogue
- **Quality Assurance**: Human oversight ensures code quality and functionality

### Development Conversation History
The `cursor-sql/` directory contains the complete development conversation history, showcasing:
- **Feature Planning**: How each feature was conceived and designed through human-AI dialogue
- **Implementation Process**: Step-by-step development with AI assistance and human guidance
- **Problem Solving**: Collaborative debugging and optimization sessions
- **Code Evolution**: How the codebase grew and improved over time through iterative refinement

**Key Development Conversations:**
- `state.sql` - Main development session with comprehensive feature implementation
- `profile-state.sql` - User profile and authentication system development
- `ad8-state.sql` - Advanced features and AI integration discussions
- `bc6-state.sql` - Backend architecture and database design
- `d5a-state.sql` - Frontend interface and user experience development
- `fa9-state.sql` - Final features and optimization sessions

These conversations demonstrate the collaborative nature of modern software development, where human creativity and AI capabilities combine to create sophisticated applications.

## 📊 Performance & Scalability

### Optimizations
- **Database Indexing**: Optimized queries for reading history
- **Caching**: Hexagram symbols and frequently accessed data
- **Async Processing**: Background tasks for image generation
- **Connection Pooling**: Efficient database connections

### Monitoring
- **Performance Metrics**: Response time tracking
- **Memory Usage**: Resource utilization monitoring
- **Error Tracking**: Comprehensive error logging
- **User Analytics**: Reading patterns and usage statistics

## 🔒 Security & Privacy

### Data Protection
- **User Authentication**: Secure login and session management
- **Data Encryption**: Sensitive data protection
- **API Security**: Rate limiting and input validation
- **Privacy Controls**: User data management and deletion

### AI Safety
- **Content Filtering**: Appropriate content generation
- **Rate Limiting**: Prevent API abuse
- **Error Handling**: Graceful failure management
- **Audit Logging**: Complete request tracking

## 🌟 Future Enhancements

### Planned Features
- **Vision Image Generation**: AI-powered visualization of mystical visions extracted from flame readings using DALL-E 3
- **Tarot Card System**: Complete tarot divination support
- **Astrology Integration**: Birth chart and planetary readings
- **Community Features**: Reading sharing and discussion

### Technical Improvements
- **Microservices Architecture**: Scalable service separation
- **Real-time Features**: WebSocket-based live readings
- **Advanced AI**: Fine-tuned models for divination

## 📚 Documentation

- **API Documentation**: Complete endpoint reference
- **Development Guide**: Contributing and setup instructions
- **Testing Guide**: Comprehensive testing documentation
- **Deployment Guide**: Production deployment instructions

## 🤝 Contributing

We welcome contributions from developers interested in the intersection of ancient wisdom and modern technology. Please see our contributing guidelines for more information.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ancient Wisdom**: Traditional I Ching and Runic practitioners
- **Modern AI**: OpenAI, Ollama, and Pinecone for their powerful tools
- **Cursor.ai**: For revolutionizing the development process
- **Open Source Community**: For the foundational technologies that make this possible
