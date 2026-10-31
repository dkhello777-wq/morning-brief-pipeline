/**
 * 제작 영상 → 구글 드라이브 자동 복사 (Google Apps Script, 팀장 구글 계정에서 실행)
 *
 * GitHub Actions(render.yml)가 영상을 만들면 공개 릴리스 render-<id> 에 status.json 과 mp4 가 올라갑니다.
 * 이 스크립트는 10분마다 릴리스 목록을 보고, 아직 안 옮긴 영상을
 * 내 드라이브 > morning-brief > 제작 영상 > <날짜> 폴더에 mp4 와 캡션(txt)으로 저장합니다.
 * 맥이나 GitHub 열쇠가 필요 없습니다.
 *
 * 처음 한 번만: 위쪽 함수 목록에서 setup 을 고르고 ▶ 실행 → 권한 허용.
 * 멈추고 싶으면: stop 을 고르고 ▶ 실행.
 */
var REPO = 'dkhello777-wq/morning-brief-pipeline';
var PARENT_FOLDER_ID = '1tFE5A7GjL_0lbrqVTxDPOHyOwUAWhAt5'; // 내 드라이브 > morning-brief (없으면 내 드라이브 맨 위)
var ROOT_NAME = '제작 영상';
var SLOT = {am: '아침', noon: '정오', pm: '저녁', breaking_1100: '속보 11시', breaking_1500: '속보 15시'};
var MAX_TRIES = 6; // 같은 릴리스가 6번(약 1시간) 연속 실패하면 건너뜀

function setup() {
  stop();
  ScriptApp.newTrigger('copyNewVideos').timeBased().everyMinutes(10).create();
  copyNewVideos();
  console.log('설정 완료: 10분마다 새 영상을 이 폴더에 복사합니다 → ' + rootFolder_().getUrl());
}

function stop() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'copyNewVideos') ScriptApp.deleteTrigger(t);
  });
}

function copyNewVideos() {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) return;
  try {
    var props = PropertiesService.getScriptProperties();
    var done = JSON.parse(props.getProperty('done') || '{}');
    var tries = JSON.parse(props.getProperty('tries') || '{}');
    var errors = [], tags;
    try {
      tags = listReleases_();
      props.deleteProperty('listFails');
    } catch (e) { // GitHub가 잠깐 안 될 때는 다음 차례에 다시 봄. 2시간 넘게 계속되면 오류로 알림
      var fails = Number(props.getProperty('listFails') || 0) + 1;
      props.setProperty('listFails', String(fails));
      if (fails >= 12) throw e;
      return;
    }
    tags.reverse().forEach(function (tag) { // 오래된 것부터
      if (done[tag]) return;
      var status = fetchJson_('https://github.com/' + REPO + '/releases/download/' + tag + '/status.json');
      if (!status) return; // 아직 만드는 중
      try {
        copyRelease_(tag.replace(/^render-/, ''), status);
        done[tag] = new Date().toISOString();
        delete tries[tag];
      } catch (e) {
        tries[tag] = (tries[tag] || 0) + 1;
        if (tries[tag] >= MAX_TRIES) { done[tag] = 'failed'; delete tries[tag]; }
        errors.push(tag + ': ' + e.message);
      }
      props.setProperty('done', JSON.stringify(keepLast_(done, 60)));
      props.setProperty('tries', JSON.stringify(tries));
    });
    if (errors.length) throw new Error('드라이브 복사 실패 ' + errors.join(' / '));
  } finally {
    lock.releaseLock();
  }
}

// 최근 릴리스 태그(render-로 시작), 최신 먼저. 공개 Atom 피드를 쓰고, 안 되면 GitHub API.
function listReleases_() {
  var res = UrlFetchApp.fetch('https://github.com/' + REPO + '/releases.atom', {muteHttpExceptions: true});
  if (res.getResponseCode() === 200) {
    var tags = [];
    res.getContentText().split('<entry>').slice(1).forEach(function (entry) {
      var m = entry.match(/<id>[^<]*\/(render-[^<\/]+)<\/id>/) || entry.match(/\/releases\/tag\/(render-[^"]+)"/);
      if (m) tags.push(m[1]);
    });
    return tags;
  }
  var list = fetchJson_('https://api.github.com/repos/' + REPO + '/releases?per_page=20');
  if (!list) throw new Error('GitHub 릴리스 목록을 못 읽음 (' + res.getResponseCode() + ')');
  return list.filter(function (r) { return !r.draft && /^render-/.test(r.tag_name); })
             .map(function (r) { return r.tag_name; });
}

function copyRelease_(id, status) {
  var m = id.match(/^(\d{4}-\d{2}-\d{2})_(.+)$/);
  var day = m ? m[1] : '기타';
  var label = m ? day + ' ' + (SLOT[m[2]] || m[2]) : id;
  var folder = subfolder_(rootFolder_(), day);
  var videos = status.videos || {}, captions = status.captions || {};
  Object.keys(videos).forEach(function (key) {
    var short = key.match(/^short(\d+)$/);
    var name = label + (key === 'main' ? '' : short ? ' 숏컷' + short[1] : ' ' + key);
    var res = UrlFetchApp.fetch(videos[key], {muteHttpExceptions: true});
    if (res.getResponseCode() !== 200) throw new Error(name + ' 영상 받기 실패 (' + res.getResponseCode() + ')');
    put_(folder, name + '.mp4', res.getBlob().setContentType('video/mp4'));
    if (captions[key]) put_(folder, name + ' 캡션.txt', Utilities.newBlob(captions[key], 'text/plain', 'caption.txt'));
    console.log('복사함: ' + ROOT_NAME + '/' + day + '/' + name + '.mp4');
  });
}

// 같은 이름 파일이 있으면(다시 만든 영상) 휴지통으로 보내고 새로 저장
function put_(folder, name, blob) {
  var old = folder.getFilesByName(name);
  while (old.hasNext()) old.next().setTrashed(true);
  folder.createFile(blob.setName(name));
}

function rootFolder_() {
  var parent;
  try { parent = DriveApp.getFolderById(PARENT_FOLDER_ID); } catch (e) { parent = DriveApp.getRootFolder(); }
  return subfolder_(parent, ROOT_NAME);
}

function subfolder_(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}

function fetchJson_(url) {
  var res = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
  return res.getResponseCode() === 200 ? JSON.parse(res.getContentText()) : null;
}

function keepLast_(obj, n) {
  var keys = Object.keys(obj), out = {};
  keys.slice(Math.max(0, keys.length - n)).forEach(function (k) { out[k] = obj[k]; });
  return out;
}
