import time
import requests
import subprocess
import signal
import json
import os
import sys
import threading
import random
from pathlib import Path
from google import genai
from google.genai import types

# 설정
PROJ_ROOT = Path("/Users/a12/projects/tts")
CONFIG_PATH = PROJ_ROOT / "config.json"
STATE_FILE = PROJ_ROOT / "core_v2" / "director_state.json"
LEARNED_FILE = PROJ_ROOT / "core_v2" / "learned_patterns.json"
LOG_DIR = PROJ_ROOT / "core_v2" / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Config 로드
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config_data = json.load(f)
    GEMINI_API_KEY = config_data.get("Gemini_API_KEY")
    LLM_PROVIDER = config_data.get("LLM_PROVIDER", "GEMINI")

# Gemini 클라이언트 초기화
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 서버 실행 커맨드
ACESTEP_CMD = "cd /Users/a12/projects/tts/ace-step-local/ACE-Step-1.5 && /Users/a12/.local/bin/uv run acestep --port 7860 --enable-api --init_service True"

# Telegram 설정
TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80" 
CHAT_ID = "7793202015"

class TokenOptimizer:
    """로컬 LLM(Ollama)을 사용하여 프롬프트를 압축하고 토큰을 절약하는 모듈"""
    def __init__(self, model="qwen2.5-coder:7b"):
        self.model = model

    def optimize(self, prompt):
        print(f"🔍 [Token Optimizer] 프롬프트 압축 중... (Provider: {LLM_PROVIDER})")
        
        # 학습된 패턴 불러오기
        rules = ""
        try:
            if LEARNED_FILE.exists():
                with open(LEARNED_FILE, "r") as f:
                    patterns = json.load(f)
                    rules = "\n".join(patterns.get("style_rules", []))
        except: pass

        system_prompt = f"You are a prompt compression expert. Shorten the following instruction into a dense, keyword-heavy prompt for AI music/image generation. Focus on minimizing token usage while preserving all core artistic details.\n\n[USER PREFERENCES]\n{rules}\n\nOutput ONLY the optimized prompt."
        
        if LLM_PROVIDER == "GEMINI" and gemini_client:
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                    contents=[f"Original: {prompt}"]
                )
                return response.text.strip()
            except Exception as e:
                print(f"Gemini Optimization Error: {e}")

        # Fallback to Ollama
        try:
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": self.model,
                "prompt": f"{system_prompt}\n\nOriginal: {prompt}",
                "stream": False
            }, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", prompt).strip()
        except Exception as e:
            print(f"Ollama Optimization Error: {e}")
        return prompt

class Watchdog:
    """에러 발생 시 최대 2회 재시도 및 로컬 모델 우회 전략을 관리"""
    def __init__(self, director):
        self.director = director
        self.max_retries = 2

    def run_with_retry(self, script_path, args=[]):
        retries = 0
        while retries < self.max_retries:
            print(f"🚀 [Watchdog] 실행 시도 {retries + 1}/{self.max_retries}: {script_path}")
            try:
                cmd = ["python3", str(script_path)] + args
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print("✅ 실행 성공")
                    return True, result.stdout
                else:
                    print(f"❌ 실행 실패 (Exit Code: {result.returncode})")
                    print(f"Error: {result.stderr}")
            except Exception as e:
                print(f"❌ 프로세스 오류: {e}")
            
            retries += 1
            if retries < self.max_retries:
                self.director.send_msg(f"⚠️ 에러 발생! {retries}회차 로컬 모델로 재시도합니다...")
                time.sleep(5)
        
        return False, "2회 재시도 모두 실패"

class IdleWorker:
    """시스템이 휴식 중일 때 배경음악 및 시나리오를 자동 생성하는 일꾼"""
    def __init__(self, director):
        self.director = director
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            print("🏭 [Idle Factory] 가동 시작")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            print("🛑 [Idle Factory] 중지됨")

    def _loop(self):
        while self.running:
            try:
                # 메인 파이프라인이 동작 중이면 대기
                if self.director.state.get("current_step") != "IDLE":
                    time.sleep(60)
                    continue

                # 1. BGM 생성 (1시간에 한 번 정도)
                if random.random() < 0.1: 
                    themes = ["웅장한 무협 결투", "애절한 이별의 해금", "평화로운 대나무 숲", "긴박한 추격전"]
                    theme = random.choice(themes)
                    print(f"🏭 [Idle Factory] 자동 BGM 생성 중: {theme}")
                    self.director.generate_solo_music(theme, is_idle=True)

                # 2. 시나리오 브레인스토밍 (Ollama 활용)
                # (생략: 향후 Ollama 연동 시 추가)
                
                time.sleep(300) # 5분마다 체크
            except Exception as e:
                print(f"⚠️ [Idle Factory] 에러: {e}")
                time.sleep(60)

class SelfHealingEngine:
    """서버의 상태를 감시하고 장애 발생 시 스스로 치유(재시작)하는 엔진"""
    def __init__(self, director):
        self.director = director
        self.last_restart_time = 0
        self.consecutive_failures = 0

    def check_and_heal(self):
        import socket
        is_port_open = False
        try:
            with socket.socket(socket.socket.AF_INET, socket.socket.SOCK_STREAM) as s:
                s.settimeout(1)
                is_port_open = (s.connect_ex(("localhost", 7860)) == 0)
        except:
            pass

        if not is_port_open:
            # 포트가 닫혀있다면 재시도 검토
            current_time = time.time()
            if current_time - self.last_restart_time > 300: # 5분 간격 보호
                print("🚨 [Self-Healing] 서버 포트 닫힘 감지. 자동 재시작을 시도합니다.", flush=True)
                self.director.send_msg("🩹 **[자가 치유]** 음악 서버가 꺼져 있어 부사장이 스스로 깨우는 중입니다.")
                self.restart_server()
                self.last_restart_time = current_time
        else:
            # 포트는 열려있으나 API 응답이 계속 실패할 경우 (데드락)
            if self.consecutive_failures >= 3:
                print("🚨 [Self-Healing] 지속적 API 실패 감지. 하드 리셋을 시도합니다.", flush=True)
                self.director.send_msg("🧨 **[하드 리셋]** 서버 응답이 꼬여있어 부사장이 강제 재부팅을 결정했습니다.")
                self.restart_server(hard=True)
                self.consecutive_failures = 0
                self.last_restart_time = time.time()

    def restart_server(self, hard=False):
        try:
            if hard:
                subprocess.run("pkill -9 -f acestep", shell=True)
                time.sleep(2)
            
            # 백그라운드에서 서버 실행
            print(f"🛠️ [Self-Healing] 명령 실행: {ACESTEP_CMD}", flush=True)
            subprocess.Popen(ACESTEP_CMD, shell=True, preexec_fn=os.setsid)
            print("✅ [Self-Healing] 서버 재시작 커맨드 발송 완료", flush=True)
        except Exception as e:
            print(f"❌ [Self-Healing] 재시작 실패: {e}", flush=True)

    def report_failure(self):
        self.consecutive_failures += 1

    def report_success(self):
        self.consecutive_failures = 0

class ReasoningEngine:
    """부사장이 행동하기 전 '생각(Chain-of-Thought)'을 하게 만드는 추론 엔진"""
    def __init__(self, director):
        self.director = director

    def think(self, user_input, context=""):
        """사용자의 지시를 분석하여 숨은 의도와 최적의 대응 전략을 도출 (JSON Output)"""
        print(f"🤔 [Reasoning Engine] 분석 중: {user_input}")
        
        system_prompt = f"""You are the Thinking Brain of an AI Director (VP). 
Before acting, you must reason through the user's request and map it to a specific command.

CONTEXT: {context}

[INTENTS]
- START_PIPELINE: Start the full production pipeline (start, go, hyeobara).
- GENERATE_SCENARIO: Write one or more scripts/scenarios. Params: {{"count": int, "topic": str}}.
- GENERATE_MUSIC: Generate a solo BGM. Params: {{"prompt": str}}.
- APPROVE: Approve the current step or say 'Next'.
- FIX: Request a fix/modification to the current result. Params: {{"instruction": str}}.
- STATUS: Check current system status or progress.
- GREET: Casual greeting or checking if alive (ya, hello, etc.).

[OUTPUT FORMAT]
Return ONLY a valid JSON object:
{{
  "thought": "Your brief reasoning in English",
  "intent": "THE_INTENT_NAME",
  "params": {{ ... }}
}}
"""
        
        if LLM_PROVIDER == "GEMINI" and gemini_client:
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json"
                    ),
                    contents=[f"User Input: {user_input}"]
                )
                res_data = json.loads(response.text.strip())
                print(f"💭 [Reasoning Engine] Gemini 분석: {res_data.get('intent')}")
                return res_data
            except Exception as e:
                print(f"Gemini Reasoning Error: {e}")

        # Basic fallback matching
        return {"thought": "Fallback to basic matching", "intent": "UNKNOWN", "params": {}}

class SelfLearningBrain:
    """국장님의 피드백과 과거 실패 사례를 분석하여 스스로 성장하는 두뇌"""
    def __init__(self, director):
        self.director = director
        self.learned_file = LEARNED_FILE
        self.patterns = self.load_patterns()

    def load_patterns(self):
        if self.learned_file.exists():
            with open(self.learned_file, "r") as f:
                return json.load(f)
        return {"music_preferences": [], "style_rules": [], "failure_lessons": []}

    def save_patterns(self):
        with open(self.learned_file, "w") as f:
            json.dump(self.patterns, f, indent=4, ensure_ascii=False)

    def learn_from_fix(self, original_prompt, fix_instruction):
        """국장님의 보완 지시를 분석하여 영구적인 스타일 규칙으로 변환 (Provider: {LLM_PROVIDER})"""
        print(f"🧠 [Learning Brain] 국장님 피드백 분석 중: {fix_instruction}")
        
        system_prompt = "Analyze the user's feedback on an AI-generated asset and distill it into a short, reusable artistic rule or 'style_rule' (max 10 words). Focus on key preferences like 'vibe', 'instruments', or 'atmosphere'. Output ONLY the rule."
        
        if LLM_PROVIDER == "GEMINI" and gemini_client:
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                    contents=[f"Original: {original_prompt}\nFeedback: {fix_instruction}"]
                )
                new_rule = response.text.strip()
                if new_rule and new_rule not in self.patterns["style_rules"]:
                    self.patterns["style_rules"].append(new_rule)
                    self.save_patterns()
                    print(f"✨ [Learning Brain] Gemini 학습 완료: {new_rule}")
                    return new_rule
            except Exception as e:
                print(f"Gemini Learning Error: {e}")

        # Fallback to Ollama
        try:
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "qwen2.5-coder:7b",
                "prompt": f"{system_prompt}\n\nOriginal: {original_prompt}\nFeedback: {fix_instruction}",
                "stream": False
            }, timeout=30)
            
            if response.status_code == 200:
                new_rule = response.json().get("response", "").strip()
                if new_rule and new_rule not in self.patterns["style_rules"]:
                    self.patterns["style_rules"].append(new_rule)
                    self.save_patterns()
                    print(f"✨ [Learning Brain] Ollama 학습 완료: {new_rule}")
                    return new_rule
        except Exception as e:
            print(f"Error learning from fix: {e}")
        return None

    def recursive_review(self):
        """저장된 수많은 스타일 규칙을 주기적으로 검토하여 더 높은 수준의 전략적 패턴 추출"""
        if len(self.patterns["style_rules"]) < 5: return

        print("🔄 [Learning Brain] 재귀적 메모리 검토 중... 고차원 패턴 추출 시작")
        rules_text = "\n".join(self.patterns["style_rules"])
        
        system_prompt = "Review these artistic rules and find common patterns. Summarize them into 3 CORE ARTISTIC VALUES that define the CEO's taste. Output ONLY the 3 values."
        
        try:
            response = requests.post("http://localhost:11434/api/generate", json={
                "model": "qwen2.5-coder:7b",
                "prompt": f"{system_prompt}\n\nRules:\n{rules_text}",
                "stream": False
            }, timeout=60)
            
            if response.status_code == 200:
                core_patterns = response.json().get("response", "").strip()
                print(f"🏆 [Learning Brain] 추출된 핵심 가치:\n{core_patterns}")
                # 핵심 가치를 최상단 규칙으로 등록
                # self.patterns["style_rules"] = [f"[CORE VALUE] {core_patterns}"] + self.patterns["style_rules"]
                # self.save_patterns()
        except Exception as e:
            print(f"Error in recursive review: {e}")

class ScenarioBrain:
    """사용자의 고차원적 명령(예: 대본 3편 적어라)을 받아 실제 대본을 창작하는 창의적 두뇌"""
    def __init__(self, director):
        self.director = director
        self.model = "qwen2.5-coder:7b"

    def write_scripts(self, count=1, topic="조선스낵 (욕심쟁이 주모와 반전 유머)"):
        print(f"✍️ [Scenario Brain] '{topic}' 컨셉으로 유머 대본 {count}편 창작 시작...")
        
        scripts = []
        for i in range(count):
            system_prompt = f"""You are a creative Screenwriter for 'Chosun Snack' style humorous shorts.
Follow the [Chosun Snack Style]:
- Theme: {topic} (Joseon Dynasty setting, Satire, Slapstick, Witty Punchlines)
- Characters: Greedy Nobleman (황대감), Clever Servant (돌쇠), or other Joseon archetypes in funny situations.
- Narrative: Short, high-tension comedic build-up leading to a 'Twist/Punchline'.
- Visual: Detailed descriptions for AI video generation (Wan 2.1/Flux style).
- Language: Authentic but humorous Joseon-era Korean dialect (사투리/고어투).

Format: 
[제목]: [Funny Title]
(Hook)
[상황 설명]: [Visual Scene Setting]
Character A : [Line with humor/emotion]
...
(Twist/Punchline)
[상황 설명]: [The Big Laugh/Action]
Character B : [The Final Punchline]

[비주얼 연출 프롬프트]
1. [Prompt for Scene 1]
2. [Prompt for Scene 2]
Language: Korean."""
            
            if LLM_PROVIDER == "GEMINI" and gemini_client:
                try:
                    response = gemini_client.models.generate_content(
                        model="gemini-2.0-flash",
                        config=types.GenerateContentConfig(system_instruction=system_prompt),
                        contents=["Generate a high-quality creative script based on the theme."]
                    )
                    script = response.text.strip()
                    scripts.append(script)
                    print(f"✅ 대본 {i+1}편 완성 (Gemini)")
                    continue
                except Exception as e:
                    print(f"Gemini Script Error: {e}")

            # Fallback to Ollama
            try:
                response = requests.post("http://localhost:11434/api/generate", json={
                    "model": self.model,
                    "prompt": system_prompt,
                    "stream": False
                }, timeout=60)
                
                if response.status_code == 200:
                    script = response.json().get("response", "").strip()
                    scripts.append(script)
                    print(f"✅ 대본 {i+1}편 완성 (Ollama)")
            except Exception as e:
                print(f"Error writing script {i+1}: {e}")
        
        return scripts

class AIDirector:
    def __init__(self):
        self.state = self.load_state()
        self.last_update_id = 0
        self.optimizer = TokenOptimizer()
        self.watchdog = Watchdog(self)
        self.idle_worker = IdleWorker(self)
        self.healer = SelfHealingEngine(self)
        self.brain = SelfLearningBrain(self)
        self.reasoning = ReasoningEngine(self)
        self.scenario_brain = ScenarioBrain(self)

    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        return {
            "current_step": "IDLE",
            "waiting_for_approval": False,
            "retry_count": 0,
            "last_action": None,
            "pipeline_data": {}
        }

    def save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=4, ensure_ascii=False)

    def send_msg(self, text):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"Error sending msg: {e}")

    def send_audio(self, audio_path, caption=""):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
        try:
            with open(audio_path, 'rb') as audio:
                files = {'audio': audio}
                data = {'chat_id': CHAT_ID, 'caption': caption}
                requests.post(url, files=files, data=data, timeout=60)
        except Exception as e:
            print(f"Error sending audio: {e}")
            self.send_msg(f"❌ 오디오 전송 실패: {e}")

    def check_server_ready(self):
        """ACE-Step 서버(7860)가 준비되었는지 확인하고 보고"""
        import socket
        try:
            with socket.socket(socket.socket.AF_INET, socket.socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex(("localhost", 7860)) == 0:
                    if not self.state.get("server_ready_reported", False):
                        self.send_msg("🎵 **[알림] ACE-Step 로컬 서버 준비 완료!**\n국장님, 이제 고속 음악 생성이 가능합니다. `/start` 혹은 `시작`을 입력해 주세요.")
                        self.state["server_ready_reported"] = True
                        self.save_state()
                        return True
        except:
            pass
        return False

    def get_updates(self):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"offset": self.last_update_id + 1, "timeout": 30}
        try:
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data["ok"] and data["result"]:
                    for update in data["result"]:
                        self.last_update_id = update["update_id"]
                        if "message" in update and "text" in update["message"]:
                            self.handle_command(update["message"]["text"])
        except Exception as e:
            print(f"Error getting updates: {e}")

    def handle_command(self, text):
        raw_text = text.strip()
        print(f"📩 CEO 지시 수신: {raw_text}")

        # [NEW] AI 기반 분석 (JSON Intent)
        context = f"Step: {self.state['current_step']}, Approved: {self.state.get('waiting_for_approval')}"
        analysis = self.reasoning.think(raw_text, context)
        
        intent = analysis.get("intent", "UNKNOWN")
        params = analysis.get("params", {})
        
        if intent == "GREET":
            self.send_msg("🫡 국장님, 살아있습니다! 무엇을 도와드릴까요? 현재 파이프라인 대기 중입니다.")
            self.report_status()
            
        elif intent == "START_PIPELINE":
            self.idle_worker.stop()
            self.start_pipeline()
            
        elif intent == "GENERATE_SCENARIO":
            count = params.get("count", 1)
            topic = params.get("topic", "조선스낵")
            self.generate_scenarios(count, topic)
            
        elif intent == "GENERATE_MUSIC":
            self.idle_worker.stop()
            prompt = params.get("prompt", "웅장한 무협 배경음악")
            self.generate_solo_music(prompt)
            
        elif intent == "APPROVE":
            self.approve_step()
            
        elif intent == "FIX":
            instruction = params.get("instruction", raw_text)
            self.request_fix(instruction)
            
        elif intent == "STATUS":
            self.report_status()
            
        else:
            # Fallback to legacy keyword matching if Gemini fails or UNKNOWN
            text_lower = raw_text.lower()
            if any(greet in text_lower for greet in ["야", "시발", "시바", "안녕"]):
                self.send_msg("🫡 국장님, 살아있습니다! (Fallback Match)")
            elif "시작" in text_lower or "생성" in text_lower:
                self.start_pipeline()
            else:
                self.send_msg(f"❓ `{raw_text}`... 부사장이 정확히 이해하지 못했습니다. 더 명확하게 말씀해 주시면 제미나이로 분석하겠습니다.")

    def report_status(self):
        msg = f"""
📊 **[AI Director] 현재 상태 보고**
- 현재 단계: `{self.state['current_step']}`
- 승인 대기 여부: `{'예' if self.state['waiting_for_approval'] else '아니오'}`
- 재시도 횟수: `{self.state['retry_count']}/2`
        """
        self.send_msg(msg)

    def start_pipeline(self):
        self.state["current_step"] = "SCRIPT_GEN"
        self.state["waiting_for_approval"] = False
        self.save_state()
        self.send_msg("🚀 파이프라인을 시작합니다. [1단계: 대본 생성] 진행 중...")
        
        # 1. 프롬프트 최적화 (로컬 자가학습 루프 예시)
        raw_prompt = "Funky 70s disco style music with slap bass and brass section, energetic and melodic."
        optimized = self.optimizer.optimize(raw_prompt)
        self.send_msg(f"⚡ [Token Diet] 프롬프트 압축 완료:\n`{optimized}`")
        
        # 2. Watchdog 기반 실행
        success, output = self.watchdog.run_with_retry(PROJ_ROOT / "core_v2" / "bgm_generator_auto.py")
        
        if success:
            self.state["waiting_for_approval"] = True
            self.save_state()
            self.send_msg("🎬 [BGM 생성 완료] 결과물을 확인하고 'Next' 혹은 '보완 [내용]'을 입력해 주세요.")
        else:
            self.send_msg(f"🚨 [긴급] 2회 재시도 모두 실패했습니다. 직접 확인이 필요합니다.\n사유: {output}")

    def approve_step(self):
        if not self.state["waiting_for_approval"]:
            self.send_msg("⚠️ 현재 승인 대기 중인 단계가 없습니다.")
            return

        current = self.state["current_step"]
        if current == "SCRIPT_GEN":
            self.state["current_step"] = "BGM_GEN"
            self.state["waiting_for_approval"] = False
            self.send_msg("✅ 대본 승인 완료. [2단계: BGM 생성] 단계로 진입합니다.")
            # BGM 생성 실행
        elif current == "BGM_GEN":
            self.state["current_step"] = "FINISHED"
            self.state["waiting_for_approval"] = False
            self.send_msg("🎉 모든 공정 승인 완료! 최종 영상 조립을 준비합니다.")
        
        self.save_state()

    def generate_scenarios(self, count=1):
        self.send_msg(f"✍️ 국장님, 대본 `{count}편` 쓰기 명령 접수했습니다. 부사장이 직접 집필 후 보고드리겠습니다.")
        scripts = self.scenario_brain.write_scripts(count)
        
        for i, s in enumerate(scripts):
            summary = s[:100] + "..." if len(s) > 100 else s
            self.send_msg(f"📝 **[대본 {i+1}편 완성]**\n\n{summary}")
            
            # 여기서 자동으로 다음 단계(음악/이미지)로 넘어가는 루프를 태울 수 있음
            # 현재는 보고 후 대기
        
        self.state["current_step"] = "SCRIPT_DONE"
        self.state["waiting_for_approval"] = True
        self.save_state()
        self.send_msg("🎬 모든 대본 집필이 끝났습니다. 승인해주시면 바로 음악 및 영상 제작에 착수하겠습니다.")

    def request_fix(self, instruction):
        self.send_msg(f"🛠️ 보완 지시를 접수했습니다: `{instruction}`\n부사장이 국장님의 취향을 학습하며 수정을 진행합니다...")
        
        # 자가 학습 루프 가동
        original = self.state.get("last_prompt", "Unknown prompt")
        learned_rule = self.brain.learn_from_fix(original, instruction)
        
        if learned_rule:
             self.send_msg(f"💡 **[자가 학습 완료]** 국장님의 취향을 이해했습니다: `{learned_rule}`\n앞으로는 이 스타일을 최우선으로 반영하겠습니다.")

        self.state["retry_count"] += 1
        self.save_state()

    def generate_solo_music(self, prompt, is_idle=False):
        if not is_idle:
            self.send_msg(f"🎹 국장님의 지시대로 음악 작곡을 시작합니다:\n`{prompt}`\n(평균 1~2분 소요됩니다.)")
            self.state["last_prompt"] = prompt
            self.save_state()
        
        # 7860 서버로 요청
        BASE_URL = "http://localhost:7860"
        payload = {
            "prompt": prompt,
            "thinking": True,
            "audio_duration": 30,
            "audio_format": "mp3"
        }
        
        try:
            res = requests.post(f"{BASE_URL}/release_task", json=payload, timeout=60)
            task_id = res.json()['data']['task_id']
            
            # 폴링
            start_time = time.time()
            while time.time() - start_time < 300: # 5분 타임아웃
                q_res = requests.post(f"{BASE_URL}/query_result", json={"task_id_list": [task_id]}, timeout=10)
                info = q_res.json()['data'][0]
                if info['status'] == 1:
                    audio_raw = json.loads(info['result'])[0]['file']
                    audio_url = f"{BASE_URL}/v1/audio?path={audio_raw}"
                    
                    # 다운로드 및 저장
                    folder = "tmp_samples" if not is_idle else "Library/bgm/factory"
                    temp_path = PROJ_ROOT / folder / f"{'request' if not is_idle else 'factory'}_{int(time.time())}.mp3"
                    temp_path.parent.mkdir(exist_ok=True, parents=True)
                    
                    audio_data = requests.get(audio_url, timeout=30).content
                    temp_path.write_bytes(audio_data)
                    
                    if not is_idle:
                        self.send_audio(temp_path, f"🎵 국장님 요청 곡 완성!\n컨셉: {prompt}")
                    else:
                        print(f"🏭 [Idle Factory] 배경음악 비축 완료: {temp_path.name}")
                    return
                elif info['status'] == 2:
                    self.send_msg("❌ 음악 생성 도중 서버 에러가 발생했습니다.")
                    return
                time.sleep(5)
            if not is_idle:
                self.send_msg("🚨 음악 생성 시간이 너무 오래 걸려 취소되었습니다.")
            self.healer.report_success()
        except Exception as e:
            self.healer.report_failure()
            if not is_idle:
                self.send_msg(f"⚠️ 음악 서버 연결 실패: {e}")
            print(f"⚠️ [Music Engine] {( 'Idle' if is_idle else 'Direct' )} Error: {e}")

    def run_loop(self):
        self.send_msg("🤖 AI 부사가 업무를 시작했습니다. (ACE-Step 서버 감시 중)")
        self.idle_worker.start()
        
        def signal_handler(sig, frame):
            print("🛑 Director 종료 요청 수신. 상태 저장 중...")
            self.idle_worker.stop()
            self.save_state()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while True:
            try:
                self.get_updates()
                self.check_server_ready()
                self.healer.check_and_heal()
                
                # 6시간마다 혹은 특정 주기로 재귀적 메모리 검토
                if random.random() < 0.001: # 루프 주기 고려
                    self.brain.recursive_review()
                    
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ 루프 오류 발생: {e}")
                time.sleep(5)

if __name__ == "__main__":
    director = AIDirector()
    if len(sys.argv) > 1 and sys.argv[1] == "--morning":
        # 기존 브리핑 기능 유지 (필요시 별도 모듈화)
        pass 
    else:
        director.run_loop()
