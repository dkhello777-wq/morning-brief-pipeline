#!/usr/bin/env python3
"""Reel performance report for the brief reels.
Usage: python3 analytics/analyze.py [snapshot.json ...]  (default: the newest file in analytics/snapshots/)
Output: analytics/report.md

A snapshot is the reels list from vidIQ `vidiq_instagram_owner_insights` (account day.brief), saved as
analytics/snapshots/YYYY-MM-DD.json with {"fetched_at", "followersCount", "reels": [...]}. Drop the signed
thumbnailUrl fields before committing. Per-episode production notes (icons, cover, hook) go in
analytics/episodes.csv, keyed by shortcode, so they can be compared once there is enough reach.
"""
import csv, json, pathlib, re, statistics, sys
from collections import defaultdict
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).parent
MIN_PLAYS = 100   # below this a reel's ratios are mostly noise
MIN_GROUP = 10    # reels per group before a comparison is worth acting on

# caption keyword -> topic; first match per issue wins (시위 first: riot captions also mention fires and injuries)
TOPICS = [
    ("시위·사회", "시위 폭동 체포 통행금지 소요"),
    ("전쟁·안보", "전쟁 드론 공습 미사일 전투기 군 투입 해협 기뢰 혁명수비대 우크라이나 러시아 이스라엘 후티 사령부"),
    ("외교·국제정치", "회담 크렘린 푸틴 제재 중재 농축 우라늄 대선 결선 개통"),
    ("국내 정치·사법", "탄핵 특검 징역 감형 내란 선관위 대법원장 국감 압수수색 확정"),
    ("사건·사고", "화재 방화 순직 흉기 검거 참사 용의자 습격 해킹 부상"),
    ("재난·날씨·보건", "호우 강풍 특보 침수 에볼라 확산"),
    ("경제·기업·AI", "머스크 테슬라 합병 과금 클라우드 AI"),
]

def load(paths):
    reels = {}
    for p in sorted(paths):  # later snapshots overwrite earlier numbers for the same reel
        snap = json.load(open(p))
        for r in snap["reels"]:
            reels[r["shortcode"]] = r | {"_followers": snap.get("followersCount"), "_fetched": snap.get("fetched_at")}
    return list(reels.values())

def issues(caption):
    return [s.strip() for s in re.split(r"[①②③④⑤]", caption)[1:]]

def topic(text):
    for name, words in TOPICS:
        if any(w in text for w in words.split()):
            return name
    return "기타"

def slot(r):
    return "아침(세계)" if "아침" in r["caption"][:20] else "저녁(국내)"

def kst(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=9)

def num(v):
    return 0 if v is None else v

def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None

def fmt(v, d=1):
    return "–" if v is None else f"{v:.{d}f}"

def group_table(rows, key, title):
    groups = defaultdict(list)
    for r in rows:
        for k in (key(r) if isinstance(key(r), list) else [key(r)]):
            groups[k].append(r)
    out = [f"### {title}", "", "| 그룹 | 편수 | 평균 조회 | 평균 시청률 % | 좋아요/조회 | 저장+공유 |", "|---|---|---|---|---|---|"]
    for k, g in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        plays = sum(num(r["playCount"]) for r in g)
        likes = sum(num(r["likeCount"]) for r in g)
        ss = sum(num(r["saves"]) + num(r["shares"]) for r in g)
        flag = "" if len(g) >= MIN_GROUP else " ⚠️"
        out.append(f"| {k}{flag} | {len(g)} | {fmt(plays/len(g))} | {fmt(mean([r['avgWatchedPct'] for r in g]))} "
                   f"| {fmt(likes/plays if plays else None, 2)} | {ss} |")
    return out + [""]

def main():
    snaps = sys.argv[1:] or sorted((HERE / "snapshots").glob("*.json"))[-1:]
    rows = load(snaps)
    rows.sort(key=lambda r: r["timestamp"])
    notes = {}
    if (HERE / "episodes.csv").exists():
        notes = {e["shortcode"]: e for e in csv.DictReader(open(HERE / "episodes.csv"))}
    for r in rows:
        r["_issues"] = issues(r["caption"])
        r["_topics"] = [topic(i) for i in r["_issues"]] or ["기타"]
        r["_lead"] = r["_topics"][0]

    plays = [num(r["playCount"]) for r in rows]
    med = statistics.median(plays)
    eng = sum(num(r[k]) for r in rows for k in ("saves", "shares", "commentCount"))
    reliable = med >= MIN_PLAYS and len(rows) >= 2 * MIN_GROUP

    L = [f"# 릴스 반응 리포트 ({rows[-1]['_fetched'][:10]})", "",
         f"- 대상: {len(rows)}편 ({kst(rows[0]['timestamp']):%m/%d} ~ {kst(rows[-1]['timestamp']):%m/%d}), "
         f"팔로워 {rows[-1]['_followers']}명",
         f"- 총 조회 {sum(plays)}, 편당 중앙값 {med:g}, 최대 {max(plays)} · 저장+공유+댓글 합계 {eng}", ""]
    if not reliable:
        L += ["> ⚠️ **아직 통계적으로 의미 있는 비교가 안 됩니다.** 편당 조회 중앙값이 "
              f"{med:g}회(기준 {MIN_PLAYS}회)이고 그룹당 편수도 {MIN_GROUP}편 미만입니다. "
              "조회 1~2회 차이는 같은 사람이 한 번 더 본 것일 수 있어서, 아래 표는 기록용으로만 보고 "
              "주제·표지·아이콘을 이 숫자만으로 바꾸지 마세요. 지금 병목은 콘텐츠가 아니라 노출(도달)입니다.", ""]

    L += ["## 편별 지표", "",
          "| 게시(KST) | 편 | 첫 이슈 주제 | 길이 | 조회 | 좋아요 | 저장 | 공유 | 댓글 | 평균 시청 | 시청률 % | 아이콘/표지 메모 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        n = notes.get(r["shortcode"], {})
        memo = " / ".join(x for x in (n.get("icons"), n.get("cover")) if x) or ""
        L.append(f"| {kst(r['timestamp']):%m/%d %H:%M} | [{slot(r)}](https://www.instagram.com/reel/{r['shortcode']}/) "
                 f"| {r['_lead']} | {r['durationSeconds']}s | {num(r['playCount'])} | {num(r['likeCount'])} "
                 f"| {num(r['saves'])} | {num(r['shares'])} | {num(r['commentCount'])} "
                 f"| {fmt(num(r['avgWatchTimeMs'])/1000)}s | {fmt(r['avgWatchedPct'])} | {memo} |")
    L += [""]

    L += ["## 그룹 비교", "", f"⚠️ = {MIN_GROUP}편 미만, 참고용", ""]
    L += group_table(rows, slot, "아침 vs 저녁")
    L += group_table(rows, lambda r: r["_lead"], "첫 이슈 주제 (표지에 걸리는 이슈)")
    L += group_table(rows, lambda r: sorted(set(r["_topics"])), "다룬 주제 (한 편에 여러 개, 캡션에서 보이는 이슈만)")
    L += group_table(rows, lambda r: "80초 미만" if r["durationSeconds"] < 80 else "80~90초" if r["durationSeconds"] < 90 else "90초 이상", "길이")
    if notes:
        L += group_table([r for r in rows if r["shortcode"] in notes],
                         lambda r: notes[r["shortcode"]].get("cover") or "기록 없음", "표지 스타일 (episodes.csv)")

    L += ["## 다음 편 체크리스트", "",
          "1. 게시 후 48시간 지나면 스냅샷을 새로 받아 이 리포트를 다시 돌린다 (인사이트가 늦게 들어옴).",
          "2. 사용한 아이콘(`out_dir/icons_used.txt`)과 표지 문구를 `analytics/episodes.csv`에 한 줄 추가한다.",
          "3. 조회 중앙값이 100회를 넘기 전까지는 주제·디자인보다 노출 실험(체험 릴스, 해시태그, 첫 3초 문구)을 우선한다.",
          "4. 그룹당 10편 이상 + 중앙값 100회 이상이 되면 위 그룹 비교를 근거로 쓴다.", ""]
    (HERE / "report.md").write_text("\n".join(L))
    print(HERE / "report.md")

if __name__ == "__main__":
    main()
