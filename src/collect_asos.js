/* 기상청 ASOS 일자료 수집 (브라우저 콘솔 실행용)
 *
 * 배경: 분석 환경의 네트워크 정책상 apis.data.go.kr 직접 호출이 막혀 있어
 *       브라우저에서 수집한 뒤 CSV로 내려받는 방식을 사용했다.
 *       네트워크가 열린 환경이라면 src/collect_asos.py 방식(requests)이 더 낫다.
 *
 * 사용법: 아래 KEY에 본인 인증키를 넣고 브라우저 콘솔에서 실행.
 *        (인증키를 이 파일에 저장하지 말 것 — .env 사용)
 */
const KEY = '<YOUR_SERVICE_KEY>';
const STN = 108;                       // 서울
const FIELDS = ['tm','avgTa','minTa','maxTa','sumRn','avgRhm','avgWs','sumGsr','sumSsHr'];
const rows = [];

async function grab(y) {
  const u = `https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList`
          + `?serviceKey=${KEY}&pageNo=1&numOfRows=400&dataType=JSON`
          + `&dataCd=ASOS&dateCd=DAY&startDt=${y}0101&endDt=${y}1231&stnIds=${STN}`;
  const r = await fetch(u).then(x => x.json());
  if (r.response.header.resultCode !== '00') throw new Error(y + ': ' + r.response.header.resultMsg);
  let it = r.response.body.items.item;
  if (!Array.isArray(it)) it = [it];
  it.forEach(o => rows.push(FIELDS.map(f => (o[f] ?? '').toString().trim()).join(',')));
}

(async () => {
  for (let y = 2013; y <= 2025; y++) await grab(y);
  rows.sort();
  const csv = FIELDS.join(',') + '\n' + rows.join('\n') + '\n';
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv'}));
  a.download = 'asos_seoul_2013_2025.csv';
  document.body.appendChild(a); a.click(); a.remove();
  console.log('rows:', rows.length);
})();
