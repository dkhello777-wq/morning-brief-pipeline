# 정오 AI 편 규칙 (아침 예약 작업이 아침 편 게시 뒤에 미리 만들어 둠)

2026-10-31 팀장 결정: 아침·저녁 편은 경제·시사로 되돌리고, AI 소식은 같은 계정(@day.brief)에 매일 12:00 "정오 AI 브리핑" 하나로 1~2주 시험 운영한다(이후 조회수를 아침·저녁 편과 비교해 AI 계정 분리를 판단). 영상은 아침 예약 작업(06:30)이 아침 편을 게시한 뒤 이 규칙대로 만들어 Macaly에 올려 두고, 게시는 정오 예약 작업이 11:57에 한다. 숏컷은 만들지 않는다.

[0. 준비] 아침 편과 같은 셸·같은 코드 파일(같은 커밋, 해시 확인 끝난 것)을 씁니다. `mkdir -p /home/claude/work/noon && cd /home/claude/work && cp build.py scene_tpl.html music.py photos.py /home/claude/work/noon/ && cp -r fonts /home/claude/work/noon/ && curl -fsSL -o noon/brief_ai_example.json https://raw.githubusercontent.com/dkhello777-wq/morning-brief-pipeline/a7ca4c77b1fc7c3720b387c5da8ce492ff7ea210/brief_ai_example.json` 후 /home/claude/work/noon 에서 아래를 진행합니다. TYPECAST_API_KEY·GEMINI_API_KEY는 아침 편에서 export한 그대로 씁니다. 화면 꼬리표 "AI NOON BRIEF"·"점심 AI 브리핑", 끝장 "매일 낮 12시 AI 브리핑", 캡션 팔로우 문구 "매일 12:00 AI 소식…", 해시태그 #AI뉴스 #인공지능은 brief.json의 "topic": "ai"(edition "am")로 자동으로 나옵니다.

[3. 내용 = 정오 AI 편]
컨셉: 모든 이슈가 "AI에서 무슨 일이 있었나 + 그게 내 일·돈·커리어에 무슨 뜻인가"에 답합니다. 겁주지 않고("AI가 다 뺏는다" 금지), 호들갑 떨지 않고("혁명", "미쳤다" 금지), "온다, 이렇게 써먹자"는 톤.
① 최근 24시간(KST 어제 정오~오늘 오전)의 세계·국내 AI 이슈 3건 — 모델·제품 출시(OpenAI, Google, Anthropic, Meta, Microsoft, Apple, Nvidia, xAI, Mistral, DeepSeek 등), 빅테크 AI 실적·투자·주가, AI와 일자리·채용, 규제(미국·EU·중국). 출처는 회사 공식 블로그·문서·공시가 먼저, 그다음 Reuters·AP·Bloomberg·CNBC·The Verge·TechCrunch·Ars Technica·The Register. 실제 기사를 열어 읽어 확인한 것만, 숫자·고유명사 정확히. 뉴스레터·요약 사이트는 찾는 용도로만 쓰고 출처로 적지 않습니다. 소문·유출·한 매체 단독·CEO 예언은 넣지 않습니다.
② 오늘 써먹기 1건("ai" 객체) — 발표 24~48시간 안에 나온, 일반인이 오늘 바로 써볼 수 있는 AI 도구·기능 하나. 공식 블로그·문서 확인. company, short, headline, point1/point1_sub(무엇을 하는지·누가 쓸 수 있는지·무료 여부), point2("~할 때 쓰면 됩니다."), point2_sub, verdict "써먹기", source, 선택 "photo"([3-1] 참고).
③ 시장("market") — 직전 거래일 미국 정규장 마감. "rows"에 3줄: 나스닥 + 그날 가장 크게 움직인 AI 관련주 2개(엔비디아·마이크로소프트·알파벳·메타·애플·아마존·TSMC 등) 각 {"name", "value"(종가), "pct"(등락률)}. headline(2~3줄), date_label(예: "10/29 마감 (KST 05:00)"), note(한 줄 해석). 토·일·월요일이면 금요일 마감 + 주간 정리.
brief.json은 brief_ai_example.json 구조("topic": "ai", edition "am", 대본 7개). 목소리는 config의 voice_id.
- 이슈 순서(맨 앞 = 표지): 1) 내 일·돈·커리어에 닿는 것(직무·채용 변화, 유료 작업을 대신하는 도구, AI주 급변, AI 서비스 가격) 2) 큰 출시나 놀라운 숫자(새 최상위 모델, 기록적 거래, 대규모 감원·채용) 3) 정책·규제.
- "hook": {"q": 질문/반전 한 줄(줄당 10자 이내, 최대 2줄, 줄바꿈은 \n), "hi": 숫자가 들어간 한 줄(9자 이내)}. 브리핑 hook = 첫 이슈의 hook과 같아도 됩니다. 형식: 나와 연결("내 직무는?", "이제 ○○도 AI가?", "월 ○만 원 아끼는 법"), 반전("알고 보니", "결국", "AI가 더 잘해서?"), 질문("~라고?", "왜 ~일까?"). 예: "AI에 돈 쏟더니\n구글이 −12%?" / "코딩 면접\n이제 안 본다?". 금지: "충격", "경악", "난리남", "~안무섭다", "일자리 다 사라진다", "AI 종말", "미쳤다", "역대급 혁명", 주가가 오른다고 약속하는 말, 한쪽 편을 들거나 국적·집단을 일반화하는 표현. 영상은 0.25초부터 이 hook을 화면 가득 크게 보여 주므로, hook의 숫자가 정확해야 합니다.
- 대본 길이(전체 60초 이내 목표): 오프닝 45자 이내 — 첫 문장은 훅 그 자체(20자 이내, 숫자 포함, 2초 안에 말할 수 있게, 화면에 뜨는 hook과 같은 질문·숫자), 이어서 한 줄 설명, 끝에 "오늘 AI, 1분 정리." 날짜, 인사, 예고 나열은 넣지 않습니다(예: "AI에 돈 쏟더니 구글이 12퍼센트? 하루 5천억 달러. 오늘 AI, 1분 정리."). 이슈별 55자 이내(숫자 있는 사실 하나 + 내 일·돈에 왜 중요한지 한 줄, "다음 소식입니다" 같은 도입 없이 사실과 숫자로 시작), 오늘 써먹기 70자 이내이고 마지막 문장은 "~할 때 쓰면 됩니다."(판단·평가 문장 금지), 시장 60자 이내, 마지막 대본은 오늘의 한 줄 + brief의 question + "댓글로 남겨 주세요. 내일도 보려면 팔로우."
- "oneliner"(마지막 장면 큰 글씨, 3~4줄): 오늘 뉴스에서 끌어낸 한 줄. 컨셉을 담아도 됩니다(예: "코딩 실력보다\n문제를 고르는 눈이\n살아남는다").
- 캡션용 필드: 각 이슈 "summary"(숫자·인물·회사·모델 이름을 풀어 쓴 2~3문장, 정치 이슈는 양측 입장을 한 구절씩), "keywords"(1~2개, # 없이). brief "question"(독자 의견을 묻는 한 줄), "keywords"(최대 3개). 질문은 두려움 대신 행동을 묻습니다: "내 일에는 언제 올까요?", "여러분이라면 어디에 써먹겠어요?", "이 기능, 돈 내고 쓸 만할까요?"

[3-1. 이슈 그림과 실사 사진] 각 이슈에 다음을 넣습니다.
- "market"에도 "photo"를 넣습니다(시장 장면도 실사 배경 + 반투명 박스): 그날 가장 크게 움직인 AI 종목의 본사 건물이나 "Nasdaq MarketSite", 날마다 바꿔 씁니다.
- "photo"(실사 사진, 반드시 시도): 그 뉴스의 핵심 인물·회사·제품·장소를 찾는 위키미디어 공용 검색어 한 줄. 영어가 잘 찾아집니다(예: "Jensen Huang", "Sundar Pichai", "Sam Altman", "Googleplex", "Microsoft Redmond campus", "Nvidia GPU", "data center"). 정확한 파일을 알면 {"file": "File:정확한 파일명.jpg"}로 지정합니다. "ai" 객체(오늘 써먹기)에도 회사·제품 검색어로 "photo"를 넣습니다. 사진은 표지·훅 화면·이슈 장면·오늘 써먹기 장면의 배경 전체에 깔리고(어두운 그라데이션 위에 흰 글씨·노란 숫자), 작가·라이선스가 화면 아래쪽과 캡션 끝("📷 사진: ...")에 자동으로 붙습니다. 자유 라이선스 사진을 못 찾거나 받지 못하면 자동으로 아래 icon을 쓰는 기존 디자인으로 대체되므로 icon 후보도 늘 넣습니다. 사진이 붙은 이슈에서는 image_prompt가 쓰이지 않습니다.
- "icon": 그 뉴스의 핵심 사물·장면을 보여주는 Fluent Emoji 3D 영어 이름 후보 2~3개 리스트, 가장 구체적인 것을 맨 앞에. 이름은 유니코드 이모지 영어 이름 그대로(AI 뉴스에 자주 쓰는 예: "Robot", "Laptop", "Desktop computer", "Mobile phone", "Brain", "Money with wings", "Money bag", "Shield", "Locked with key", "Briefcase", "Classical building", "Balance scale", "Factory", "Satellite antenna", "Electric plug", "Handshake", "Megaphone", "Graduation cap", "Light bulb", "Gear"). 해외 이슈는 후보 맨 끝에 그 나라 국기 이모지(예: "🇺🇸")를 넣어도 됩니다. 얼굴 이모지와 뉴스와 무관한 범용 기호(🌍, ⚠️, 📈, ❗)는 쓰지 않습니다.
- "motion": 이동·물류 "drive", 경보·보안 사고 "pulse", 폭락·충돌 "shake", 판결·협상·정책 "sway", 돈·주가·가격 "spin", 그 밖 "bob".
- "ill": 막대 비교·다리·숫자 카운트가 의미 있을 때만 bars/bridge/alert/number(소수점도 그대로 셈, 예: 12.6), 그 외에는 {"kind": "icon"}. globe·trend는 쓰지 않습니다.
- 그날 가장 큰 이슈 한 건에만 "image_prompt": 영어 한 문장으로 장면이나 사물을 묘사(실존 인물·얼굴·로고·글자·국기 문양 없이). 사진이 없을 때만 쓰입니다.

[3-2. 오타 검수 — 빌드 전에 반드시] 브리핑의 표지·자막·음성·캡션은 모두 brief.json 글자에서 나오므로(화면 자막은 scripts 글자 그대로 나옵니다), 빌드 전에 화면·음성에 나가는 글자를 한 줄씩 뽑아 직접 읽습니다. 아래 명령으로 proof.txt를 만듭니다(줄바꿈은 ⏎로 표시됨).
```
python3 - brief.json <<'EOF' > proof.txt
import json,sys
SKIP={'voice_id','image_prompt','icon','motion','kind','video_url','permalink','icons_used','photo'}
def w(p,v):
    if isinstance(v,dict):
        for k,x in v.items():
            if k not in SKIP: w(f'{p}.{k}',x)
    elif isinstance(v,list):
        for i,x in enumerate(v): w(f'{p}[{i}]',x)
    elif isinstance(v,str): print(p,'|',v.replace('\n',' ⏎ '))
    elif isinstance(v,(int,float)): print(p,'|',v)
w('',json.load(open(sys.argv[1])))
EOF
```
proof.txt를 Read로 열어 모든 줄을 끝까지 읽고 다음을 brief.json에서 고칩니다. (1) 오타·잘못 친 글자·깨진 자모·받침이 틀린 글자·띄어쓰기 실수(실제 사례: "113.17하러"→"113.17달러", "메탁 −7%"→"메타 −7%", "시자으로"→"시작으로", "움돌았고"→"웃돌았고", "성장읈"→"성장을"). summary·question 같은 캡션용 문장도 대본과 똑같이 한 글자씩 읽습니다. (2) 인물·기업·모델·기관 이름이 기사 표기와 같고, 같은 이름이 모든 필드에서 똑같이 쓰였는지(예: "제미나이 4 카본"을 어디서는 "Gemini 4 Carbon"으로 쓰지 않기, 한글 표기로 통일). (3) 같은 사실의 숫자·단위·부호가 headline·stat·ill·market·scripts·summary 사이에서 일치하는지(예: 대본 8%와 summary 5~8%처럼 다르면 하나로 맞춤). (4) ⏎ 줄바꿈이 단어나 숫자 중간을 끊지 않는지. (5) 대본(scripts)은 소리 내어 읽었을 때 어색한 기호(%, &, ·, $)와 영문 이름이 TTS에 맞게 풀어 쓰였는지(예: "챗GPT", "클로드", "엔비디아", "90억 달러"). 고쳤으면 proof.txt를 다시 만들어 한 번 더 처음부터 읽습니다. 고친 항목은 보고에 "오타 수정: 원래→고침"으로 적고, 없으면 "오타 없음"으로 적습니다.

[4. 빌드]
① 반복 방지: Drive videos 폴더(config.drive_videos_folder_id)에서 가장 최근 brief json 6개(_am·_noon·_pm 모두)를 읽어 각 이슈의 "icons_used" 값(없으면 "icon" 후보의 첫 값)을 모아 recent_icons.txt 에 한 줄에 하나씩 저장(없으면 빈 파일). 최근 brief에서 이미 다룬 AI 소식은 다시 고르지 않습니다. 특히 오늘 아침 편(YYYY-MM-DD_am.json)의 "ai" 객체(새로운 AI 기술)와 같은 소식·도구는 고르지 않습니다.
② 그림·사진 확인: `CHECK_ART=1 RECENT_ICONS=recent_icons.txt python3 build.py brief.json out` 의 "art 1/2/3"·"art ai"·"art market" 줄을 봅니다. "PHOTO <작가·라이선스>"면 사진이 붙은 것입니다(받은 사진은 out/photo*.img로 저장되어 이후 빌드가 재사용). 사진 대신 아이콘 이름이 나오면 photo 검색어를 더 일반적인 영어(회사 이름, 본사 건물, CEO 이름)로 한 번 바꾸고 out/photo{번호}.* 를 지운 뒤 다시 확인합니다. "photo fetch failed"가 계속 나오면(네트워크 차단) 사진 없이 아이콘으로 진행하고 보고에 적습니다. "none"이 있으면 icon 후보 이름을 다른 실제 이모지 이름으로 바꿔 재확인(최대 2회).
③ 브리핑: `RECENT_ICONS=recent_icons.txt python3 build.py brief.json out`. 출력에 "WARN length"가 있으면 대본을 줄여 out/v*.mp3를 지우고 한 번 다시 빌드합니다(그래도 넘으면 그대로 진행하고 보고에 길이를 적음). 대본을 줄였으면 [3-2] 검수를 그 대본에 다시 합니다. 출력의 "music <스타일>" 줄에서 오늘의 배경 음악 이름을 기록합니다.
④ 확인: out/cover.jpg와 preview PNG를 열어 표지 위쪽에 오늘 날짜와 "AI NOON BRIEF"가 맞게 나왔는지, 훅 두 줄이 잘리지 않았는지, 이슈·시장 장면 그림이 뉴스와 맞는지, 화면 글자에 [3-2] 기준의 오타가 없는지 봅니다. 사진이 깔린 장면은 사진이 그 뉴스의 인물·회사·장소가 맞는지(엉뚱한 사람·건물·동명이인이면 photo를 더 구체적으로 바꾸거나 {"file": ...}로 지정하고 out/photo{번호}.* 를 지운 뒤 다시 빌드, 맞는 사진이 없으면 그 이슈의 photo를 빼서 아이콘으로), 사진 위 글자가 잘 읽히는지, 화면 아래쪽에 작가·라이선스 표기가 보이는지도 봅니다. preview_1.png(훅 화면)에서 훅 질문과 숫자가 크게 잘리지 않고 나오는지, preview PNG 아래쪽 자막이 대본과 같고 화면 밖으로 넘치지 않는지, 시장 장면에 rows 3줄이 이름과 함께 나오는지도 봅니다. 여기서 오타가 보이면 brief.json을 고치고 해당 빌드를 다시 합니다(대본을 고쳤으면 그 장면의 out/v*.mp3를 지우고 다시 빌드).
⑤ 실행 거부 대응: 아침 편 지시문의 실행 거부 대응과 같게 합니다(우회 금지, 코드를 읽고 최대 2번 재시도). 그래도 거부되면 brief.json만 Drive에 YYYY-MM-DD_noon.json으로 저장("video_url" 없이)하고 보고합니다.
⑥ 캡션 최종 검수(게시 직전 반드시): ④에서 brief.json을 고쳤으면 브리핑을 다시 빌드합니다. 그다음 out/caption.txt를 Read로 열어 처음부터 끝까지 한 글자씩 읽고, 받침이 틀렸거나 없는 단어가 된 글자(실제 사례: "움돌았고"→"웃돌았고", "성장읈"→"성장을", "시자으로"→"시작으로")와 [3-2] 기준의 오타가 없는지, 사진을 썼다면 "📷 사진:" 줄이 있는지, 끝에 #AI뉴스·#인공지능이 붙었는지 확인합니다. 오타가 있으면 캡션 파일을 손으로 고치지 말고 brief.json을 고친 뒤 해당 빌드를 다시 해 캡션을 새로 만들고, 다시 처음부터 읽습니다. 아래 [5] 저장의 "caption"에는 마지막으로 확인한 파일 내용을 그대로 넣습니다.

[5. 올려 두기 — 게시는 하지 않음]
a) `mcp__Macaly_Cloud__upload_file`(chatId=config.macaly_chat_id, localPath=/home/claude/work/noon/out/final.mp4, contentType video/mp4, fileSize=실제 바이트) 후, 아침 편과 같은 기준으로 curlCommand를 확인하고 실행합니다.
b) brief.json에 "video_url"(공개 URL), "caption"(out/caption.txt 최종 내용 그대로), "icons_used", "publish_slot": "12:00" 을 넣어 Drive videos 폴더에 YYYY-MM-DD_noon.json으로 저장합니다(create_file). mp4는 Drive에 올리지 않습니다.
c) 아침 편 보고 끝에 "정오 AI 편 준비: AI 소식 3건 제목, 표지 hook, 길이(초), 사진 여부, 오타 검수 결과" 2줄을 덧붙입니다. 정오 편이 실패해도 아침 편 게시는 그대로 둡니다.
