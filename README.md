# 🔍 CrewAI Research Assistant

A powerful research assistant built with CrewAI, Exa, and Streamlit that helps you research any topic using AI Agents.

![CrewAI Logo](https://cdn.prod.website-files.com/66cf2bfc3ed15b02da0ca770/66d07240057721394308addd_Logo%20(1).svg)

![App Screenshot](app.png)

## 🌟 Features

- 🤖 Multiple LLM Support
- 🔍 Advanced answering capabilities using Exa
- 📊 Real-time research process visualization
- 📝 Structured research reports
- 🎯 Topic-focused research and analysis
- 🔒 Secure API key management
- 📱 Responsive and modern UI

## 📚 Code Organization

- **Main Application (`streamlit_app.py`)**:
  - Configures the Streamlit interface
  - Manages the research workflow
  - Handles result display

- **Research Component (`researcher.py`)**:
  - Configures LLM providers (OpenAI, GROQ, Ollama)
  - Creates research agents with appropriate tools
  - Defines research task structure
  - Manages the research execution process

- **Sidebar Component (`sidebar.py`)**:
  - Handles model selection UI
  - Manages API key input
  - Integrates with local Ollama instance
  - Provides configuration options

- **Output Handler (`output_handler.py`)**:
  - Captures and formats research process output
  - Manages real-time display updates


## 🛠️ Project Structure

```
crewai-streamlit-demo/
├── streamlit_app.py # Main Streamlit application entry point
├── requirements.txt # Project dependencies
└── src/
├── components/
│ ├── researcher.py # Research agent and task implementation
│ │ # - LLM configuration
│ │ # - Research task creation
│ │ # - Exa search integration
│ └── sidebar.py # Sidebar UI and configuration
│ # - Model selection
│ # - API key management
│ # - Ollama integration
└── utils/
└── output_handler.py # Process output management
   # - Real-time output capture
   # - Output formatting
```

## 📋 Requirements

- Python >=3.10 and <3.13
- OpenAI API key or GROQ API key
- Exa API key
- Streamlit

## 🚀 Getting Started

1. Clone the repository:
```bash
git clone https://github.com/tonykipkemboi/crewai-streamlit-demo.git
cd crewai-streamlit-demo
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
conda activate isdagent
streamlit run main.py
```

## 🔑 입장코드 설정

아이디·비밀번호 대신 공용 입장코드를 입력해 입장합니다. 인증 전에는
메인·요약·분석·정리 페이지에 접근할 수 없습니다.

`.streamlit/secrets.toml`의 최상위 항목(다른 `[섹션]`보다 위)에 다음을 추가하세요.
실제 코드는 Git에 커밋하지 않습니다.

```toml
ENTRY_CODE = "사용할-입장코드"
```

환경변수 `ENTRY_CODE`를 설정하면 위 파일보다 우선합니다. 배포 환경에서도
Secrets 또는 환경변수에 코드를 설정해야 합니다. 미설정 또는 빈 코드는 입장을
차단합니다. 설정 변경 후 앱을 재시작하면 새 코드가 적용됩니다.

인증은 브라우저 세션 동안 유지되며, 새 세션에서는 다시 입력합니다.
사이드바의 **나가기**는 인증과 업로드·분석 결과 등 현재 작업 내용을 초기화합니다.
공용 코드는 개인 계정을 구분하지 않으며, 각 세션에는 별도 UUID를 부여합니다.

인증 회귀 테스트: `python -m unittest discover -s test -p 'test_auth.py'`

## 📖 메인 페이지 사용 매뉴얼

메인 페이지의 **시작하기** 버튼 아래에서 **사용 매뉴얼**을 펼쳐볼 수 있습니다.
본문은 `docs/ISD-Agent-manual.md`에서 관리하며, 내용을 수정하면 페이지에 반영됩니다.
이미지는 Markdown 파일 기준 상대 경로를 사용해 `![설명](images/manual/step-01.png)`처럼
독립된 줄에 작성합니다. 설명은 이미지 아래 캡션으로 표시됩니다.

`docs/images/manual/step-01.png`부터 `step-16.png`까지는 `docs/`의 원본 PDF에서
본문 순서로 추출한 이미지입니다. 투명도 마스크를 합성해 원래 해상도로 저장했습니다.
화면에서는 이미지 비율을 유지하며 컨테이너 너비에 맞춰 표시합니다.
스크린샷 속 글자의 추가 압축 손실을 피하도록 PNG 형식을 유지합니다.
PDF 추출 도구는 앱 실행에 필요하지 않습니다. 배포할 때 Markdown과 이미지 폴더를
함께 포함해야 합니다. 첫 로그인 이미지는 이전 버전이므로 본문에 현재 입장코드
방식을 안내했습니다.

검증: Streamlit 1.46.1에서 인증 회귀 테스트 7개와 매뉴얼 렌더링 확인을 통과했습니다.
Chrome의 1440px·390px 화면에서 접기·펼치기, 이미지 16장 로딩·화면 내 표시,
단계 번호 1~11과 분석 파일 링크 3개를 확인했습니다.

## 🔑 API Keys Setup

The application requires the following API keys:

1. **OpenAI API Key** or **GROQ API Key**
   - For OpenAI: Get it from [OpenAI Platform](https://platform.openai.com/)
   - For GROQ: Get it from [GROQ Console](https://console.groq.com/)

2. **Exa API Key**
   - Get it from [Exa](https://exa.ai)

Enter these keys in the sidebar of the application when prompted.

## 🎯 Usage

1. Open the application in your web browser
2. Select your preferred LLM provider (OpenAI or GROQ)
3. Enter your API keys in the sidebar
4. Type your research query in the text area
5. Click "Start Research" to begin the research process
6. View the real-time research process and final results

## 💡 Features in Detail

### Research Agent
The research agent (`src/components/researcher.py`) is powered by CrewAI and configured to:
- Conduct thorough research on given topics
- Analyze and summarize information
- Provide structured reports with key findings

### Process Output
The output handler (`src/utils/output_handler.py`) provides:
- Real-time process visualization
- Clean, formatted output
- Progress tracking

### User Interface
The application features a modern, responsive UI with:
- Intuitive sidebar configuration
- Clear process visualization
- Organized research results
- Professional styling

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [CrewAI](https://crewai.com) for the AI agent framework
- [Exa](https://exa.ai) for advanced search capabilities
- [Streamlit](https://streamlit.io) for the web interface

---
Made with ❤️ using CrewAI, Exa, and Streamlit
