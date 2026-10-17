# 빌드 방법

번역 대본·원문·그림 편집 명세는 저장소에 없으므로, 아래는 자신이 가진 원본과 번역 파일로 다시 빌드하는 절차입니다.

## 준비물
- 원본 `Youkai Sangokushi (Japan) Decrypted.3ds` (MD5 `ea1c1c336229a1bb5920d34f2d759b3a`)
- Python 3.12+ : `pip install pillow numpy opencv-python-headless capstone`
- 글꼴 `NanumSquareNeo-cBd.ttf`, `-dEb.ttf`, `-eHv.ttf`
- (그림 글자 검출) .NET 6 SDK + Windows 일본어 OCR

## 폴더 구성
```
<작업 폴더>/                원본 .3ds, NanumSquareNeo-*.ttf
  <이 저장소>/
    tools/
    dec/  ext/              추출물 (아래 2단계)
    tr/items.json           추출한 원문 목록
    tr/out/*.json           번역 {id: 한국어}
    tr/img/*.png            교체할 텍스처(키 "NNNNN_인덱스" 또는 "NNNNN_이름.bflim")
```

## 순서
1. 추출: `python tools/ctr.py "<원본>.3ds" ext`, `python tools/codeblz.py ext/exefs/.code ext/code.bin`, `python tools/link.py ext/romfs/Data/LINKDATA_A.BIN dec`
2. 원문 목록: `python tools/extract.py` → `tr/items.json`. 번역 묶음: `python tools/mkchunks.py`
3. 번역 작성 후 검사: `python tools/check.py tr/chunks/<묶음>.json tr/out/<묶음>.json`
4. 그림 글자: `python tools/dumpall.py` + `tools/ocr` 로 대상 검출, 배너·이름판·로고는 `banner.py`/`plate.py`/`logo.py`, 나머지는 `tr/edits/*.json` 명세를 `python tools/apply_edits.py` 로 적용 → `tr/img/`
5. 빌드: `python tools/final.py` → 작업 폴더에 `Youkai Sangokushi (Korean).3ds`
6. 차분: `xdelta3 -e -0 -S none -A -s 원본.3ds 한글.3ds 패치.xdelta` (압축 옵션 없이)
