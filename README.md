# 요괴삼국지 (3DS) 비공식 한글패치

닌텐도 3DS 일본판 **妖怪三国志** 비공식 한국어 패치입니다. 이 저장소에는 제작 도구와 기술 문서만 있고, 패치 파일(xdelta)은 [Releases](../../releases)에서 받을 수 있습니다. 게임 원본·일본어 원문·번역 대본은 포함하지 않습니다.

## 적용 방법
1. 아래 해시와 일치하는 **원본 `.3ds`**(복호화된 카트리지 덤프, 1GB)를 준비합니다. CIA나 암호화된 덤프에는 적용할 수 없습니다.
   - PowerShell: `Get-FileHash -Algorithm MD5 -LiteralPath '.\Youkai Sangokushi (Japan) Decrypted.3ds'`
2. xdeltaUI 같은 도구로 원본에 xdelta를 적용합니다. 원본 판본에 맞는 것을 고르세요(결과물은 같음).
   - `YoukaiSangokushi_3DS_KO_v1.0.xdelta`: NoCrypto 표시가 꺼진 복호화 덤프용
   - `YoukaiSangokushi_3DS_KO_v1.0_NoCrypto.xdelta`: GodMode9 등으로 복호화해 NoCrypto 표시가 켜진 덤프용
   - 「target window checksum mismatch」 오류가 나면 다른 쪽을 적용하세요. 빈 공간을 잘라낸(트림) 덤프에도 적용됩니다.
   - 명령줄: `xdelta3 -d -s "Youkai Sangokushi (Japan) Decrypted.3ds" YoukaiSangokushi_3DS_KO_v1.0.xdelta "Youkai Sangokushi (Korean).3ds"`
3. 만들어진 `.3ds`를 Azahar 등 3DS 에뮬레이터에서 실행합니다.

| 항목 | 값 |
| --- | --- |
| 원본 3DS 크기 | 1,073,741,824 바이트 |
| 원본 3DS MD5 | `ea1c1c336229a1bb5920d34f2d759b3a` |
| 원본 3DS SHA-256 | `d6dfb65e270d211554430cf320c9e1aa991b2c092807aac612e729b065e79f6b` |
| xdelta SHA-256 | `4ca76289a8383fbba0d467c94cf6981347c7fce2f970ad8411d35c01308c6b0a` |
| (NoCrypto 판본) 원본 3DS MD5 | `53cfafc00a4cde66adc6c1544112b881` |
| (NoCrypto 판본) 원본 3DS SHA-256 | `bc6020ba1211a3b7c7a11c12c11041a82861ea2ad2aad30fef5b70ca259bc67a` |
| (NoCrypto 판본) xdelta SHA-256 | `60497d6b9cef72629d535e11a4996510dc316ff0c60109b31c0ba459d10fd01b` |
| 결과 3DS 크기 | 899,928,064 바이트 |
| 결과 3DS SHA-256 | `2869e803f2d6ce707f9a3c502b3c10bdfd266e22068e7bc20b3a44f5b1e33911` |

## 주의
- 결과 파일은 복호화 상태(NoCrypto)이고 실행 코드(`.code`)를 비압축으로 넣었습니다. **에뮬레이터 기준으로 검증**했으며, 실기(커스텀 펌웨어)에서의 동작은 확인하지 않았습니다.
- 원본 덤프는 복호화되어 있지만 NoCrypto 표시가 꺼져 있어 그대로는 Azahar에서 실행되지 않습니다. 패치 결과물에는 이 표시를 켜 두었습니다.
- 결과 파일은 원본의 빈 공간(패딩)을 잘라내 원본보다 작습니다.

## 한글화 내용
- 게임 텍스트 고유 문장 약 2만 개: 대사·이벤트, 전투 대사, 무장 요괴 이름·소개, 기술·스킬·아이템 이름과 설명, 퀘스트, 메뉴, 시스템 메시지, 도움말, 크레딧
- 컷신 음성 자막
- 그림으로 된 글자 752장: 타이틀 로고, 타이틀·메뉴 버튼, 필살기 이름 배너, 무장 요괴 이름판, 지명, 도움말 그림, 장 제목, 장 끝 말풍선 등
- 게임 자체 폰트(16·14·12px)에 한글 KS X 1001 2,350자를 넣었습니다(나눔스퀘어네오 Bold).
- 이름 입력 키보드: 가나 자리에 한글 음절을 배치해 한글 이름을 입력할 수 있습니다(첫 면 기본 음절, 둘째 면 받침 음절, '바꾸기' 버튼으로 된소리·거센소리 등 변환).
- 고유명사: 삼국지 인명·지명·사건은 한국 한자음, 요괴 이름은 한국판 공식 명칭을 아는 경우 그것을, 나머지는 음역하거나 말장난을 살려 옮겼습니다.

## 그대로 둔 것
- 노래(랩) 가사 자막 한 구간은 비워 두었습니다.
- 도움말 그림 속 게임 화면 캡처나 배경 간판의 몇 픽셀짜리 아주 작은 글자
- 이름 입력은 약 170개의 정해진 음절 안에서만 고를 수 있습니다(자모 조합 입력 아님).

## 검증 범위
Azahar에서 부팅, 타이틀, 일기 선택, 이름 입력, 오프닝 대사, 튜토리얼 전투 일부, 지도 화면까지 확인했습니다. 전체 플레이 검증은 하지 않았습니다. 문제를 발견하면 Issues에 알려 주세요.

## 문서
- [CHANGELOG.md](CHANGELOG.md) — 변경 기록
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — 파일 형식과 한글화 방법
- [docs/BUILD.md](docs/BUILD.md) — 직접 빌드하는 방법
- [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md) — 글꼴
- [RIGHTS.md](RIGHTS.md) — 권리 및 외부 자료
