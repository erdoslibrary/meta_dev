# 002 뷰어 구현 참고

- 용도: `/speckit-plan`과 구현 세션의 참고 자료. `guidline.md`에서 필요한 내용을 옮겼다.
- 우선순위: 헌법, spec, plan과 다르면 그 문서가 우선한다. 충돌하면 멈추고 묻는다.
- 상태: 로딩 방식, 폴더 이름, 렌더링 방식은 plan에서 확정한다. 아래 구성은 시험을 통과한 후보이며, `viewer/`는 예시 이름이다.
- 기준: 2026-11-04, Chrome 146, Node 24.13.1. 시험 수치는 가이드 작성 시 기록이며, 로그 읽기 방식은 시험하지 않았다.

## 1. plan 근거

고정 버전: `typescript 5.9.3`, `three 0.185.0`, `@types/three 0.185.0`.

- TypeScript 7.0.2는 `outFile`과 `module: none`이 제거되어 단일 출력이 실패한다.
- three 0.186 이상은 `three.cjs`가 내용 없는 631바이트 파일이라 `file://`에서 불러올 수 없다.

Chrome 146의 `file://` 시험 결과:

| 방식 | 결과 |
|---|---|
| `<script type="module">` + importmap | CORS 차단 |
| `fetch`로 로컬 JSON 읽기 | CORS 차단 |
| `TextureLoader`로 로컬 사진 읽기 | CORS 차단 |
| 일반 `<script src>` + `three.cjs` | 동작 |
| `CanvasTexture`로 그린 재질 | 동작 |
| `<img>`로 로컬 사진 표시 | 동작 |

렌더링: `render()` 1회 호출 페이지는 5번 중 1번 컨텍스트가 끊겨 화면이 비었고, `requestAnimationFrame` 반복 페이지는 5번 모두 정상이었다. 표본이 적어 원인은 단정하지 않는다. 반복 렌더링과 `webglcontextrestored`에서의 재구성을 plan에서 검토한다.

2026-11-04 재시험: `requestAnimationFrame` 반복 페이지도 24번 중 2번 끊겼으므로 반복 렌더링만으로는 부족하다. `webglcontextlost`에서 `preventDefault()`를 호출하지 않은 1번은 복구되지 않았고, 호출한 1번은 복구되었다. three.js의 복구 처리 범위는 시험하지 않았다.

로그 읽기 방식(파일 선택 또는 생성된 JS 파일)은 plan에서 정하고 검증 방법을 포함한다.

## 2. 시험을 통과한 빌드 구성

`viewer/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "es2020",
    "module": "none",
    "moduleResolution": "node10",
    "outFile": "dist/app.js",
    "strict": true,
    "types": ["three"],
    "lib": ["es2020", "dom"],
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

`viewer/src/three-global.d.ts`: 소스에서 `import` 없이 `THREE`를 쓸 수 있게 한다.

```ts
import * as _THREE from "three";
declare global { export import THREE = _THREE; }
```

`viewer/index.html`의 스크립트 부분. 순서를 바꾸지 않는다.

```html
<script>var module = { exports: {} }, exports = module.exports;</script>
<script src="vendor/three.cjs"></script>
<script>window.THREE = module.exports;</script>
<script src="dist/app.js"></script>
```

빌드는 리포 루트에서 실행한다.

```zsh
viewer/node_modules/.bin/tsc -p viewer
```

`tsc`가 `SyntaxError: Unexpected token '?'`로 실패하면 시스템 Node 12로 실행된 것이다. Node 24는 대화형 zsh에서만 기본값으로 잡힌다(2026-11-04 확인). 새 터미널에서 `node -v`가 v24.13.1인지 확인하고 그 터미널에서 Muse를 시작한다.

## 3. 구현 세션 시작 지시문

`/speckit-implement` 전에 Muse에 붙여 넣는다. 폴더 이름이 `viewer/`가 아니면 경로를 plan에 맞춘다.

```text
이 세션은 specs/002-map-ghost-viewer/tasks.md 순서대로 구현한다.
.specify/memory/constitution.md(v1.2.0)가 스킬의 기본값보다 우선한다.
- web3d와 threejs 스킬은 기법 참고로만 쓴다. 그 스킬의 비평 라운드, 휴대폰 검사, 완료 규칙은 실행하지 않는다.
- check_page.py를 쓰지 않고 Playwright를 설치하지 않는다. 셸에서 Chrome을 실행하지 않는다. 화면 확인은 playwright MCP로만 한다.
- CDN, importmap, ES 모듈, 로컬 서버, fetch 로컬 읽기, 사진의 WebGL 텍스처 사용을 금지한다.
- npm 명령을 실행하지 않는다. 빌드는 viewer/node_modules/.bin/tsc -p viewer 만 쓴다.
- pip install을 포함해 패키지를 설치하지 않는다. 환경 문제로 명령이 실패하면 설치로 해결하지 말고 원문과 함께 보고한다.
- 테스트 게이트는 .venv/bin/python -m unittest discover tests -v 로 실행한다. python, python3를 직접 쓰지 않는다.
- 커밋하지 않는다.
```

## 4. 사람이 실행할 환경 준비

아래 명령은 Muse 밖의 일반 터미널에서 실행한다. Muse는 대신 실행하지 않는다. plan 승인 뒤, 구현 직전에 진행한다.

### 리포 연결

폴더 이름 확정 후 리포 루트에서 실행한다.

```zsh
RT_ROOT="/goinfre/$USER/realtosim"
mkdir -p viewer/vendor viewer/src "$RT_ROOT/shots"
cp "$RT_ROOT/viewer-tools/package.json" "$RT_ROOT/viewer-tools/package-lock.json" viewer/
cp "$RT_ROOT/viewer-tools/node_modules/three/build/three.cjs" viewer/vendor/
ln -sfn "$RT_ROOT/viewer-tools/node_modules" viewer/node_modules
ln -sfn "$RT_ROOT/shots" .shots
```

`.gitignore`에 아래 두 줄을 추가한다. 끝에 `/`를 붙이면 심볼릭 링크를 제외하지 못한다.

```gitignore
node_modules
.shots
```

뷰어 폴더에서 `npm install`이나 `npm ci`를 실행하지 않는다. `npm ci`는 심볼릭 링크를 실제 폴더로 바꿔 약 60MB를 홈에 설치한다. npm 명령은 goinfre의 `viewer-tools`에서만 실행한다.

### Playwright MCP 설치

```zsh
RT_ROOT="/goinfre/$USER/realtosim"
mkdir -p "$RT_ROOT/playwright-mcp" "$RT_ROOT/shots"
cd "$RT_ROOT/playwright-mcp"
npm init -y
npm install --ignore-scripts --save-exact @playwright/mcp@0.0.84
```

```zsh
cat > "$RT_ROOT/playwright-mcp/config.json" <<'EOF'
{
  "browser": {
    "browserName": "chromium",
    "isolated": true,
    "launchOptions": {
      "channel": "chrome",
      "headless": true,
      "args": ["--enable-unsafe-swiftshader"]
    }
  }
}
EOF
```

`--enable-unsafe-swiftshader`는 시험을 통과한 구성이므로 유지한다. 다만 끊김을 막아 주지는 않는다. 2026-11-04 재시험(MCP 서버 직접 호출)에서 옵션 있음은 13번 중 2번, 없음은 13번 중 1번 끊겼고, 없을 때도 SwiftShader로 렌더링되었다. 끊김 3번은 모두 시험 묶음의 첫 실행이었으며 원인은 단정하지 않는다. 첫 스크린샷의 캔버스가 비어 있으면 콘솔의 `CONTEXT_LOST_WEBGL` 경고를 확인하고 다시 찍는다.

변경 사유: "옵션을 빼면 캔버스가 하얗다"는 기존 설명이 재시험에서 재현되지 않았다.

### Muse에 등록

기존 설정을 `settings.json.bak`으로 백업한 뒤 항목을 추가한다. 등록 후 Muse를 다시 실행한다.

```zsh
RT_ROOT="$RT_ROOT" RT_NODE="$(command -v node)" python3 - <<'EOF'
import json, os, shutil
path = os.path.expanduser("~/.config/muse/settings.json")
root = os.environ["RT_ROOT"]
shutil.copy(path, path + ".bak")
data = json.load(open(path))
data.setdefault("mcpServers", {})["playwright"] = {
    "type": "stdio",
    "command": os.environ["RT_NODE"],
    "args": [
        root + "/playwright-mcp/node_modules/@playwright/mcp/cli.js",
        "--config", root + "/playwright-mcp/config.json",
        "--allow-unrestricted-file-access",
        "--output-dir", root + "/shots",
    ],
    "mode": "optional",
}
json.dump(data, open(path, "w"), indent=2, ensure_ascii=False)
print("등록 완료:", path)
EOF
```

`--allow-unrestricted-file-access`를 쓰면 브라우저가 로컬 파일 전체에 접근할 수 있다. 이 MCP로 외부 사이트를 열지 않는다.

### 동작 확인

리포 루트에서 실행한다. SwiftShader 렌더러 이름이 나오고 스크린샷 내용을 설명하면 성공이다.

```zsh
muse exec --reasoning-effort low --max-model-steps 8 \
  "playwright MCP로 about:blank를 열고 WebGL 컨텍스트를 만들어 UNMASKED_RENDERER_WEBGL 값을 알려줘. 그다음 browser_take_screenshot을 filename .shots/hello.png 로 찍고 read_file로 열어 무엇이 보이는지 한 문장으로 말해줘. 파일을 수정하지 마."
```

## 5. 구현 중 화면 확인

구현 세션을 키우지 않도록 새 세션으로 분리한다. 리포 루트에서 실행하고 `<...>`를 채운다.

```zsh
muse exec --reasoning-effort low --max-model-steps 14 \
  "파일을 수정하지 말고 다음을 확인해줘. playwright MCP로 file://$PWD/viewer/index.html 을 연다. 1) 콘솔 error와 warning을 모두 읽는다. 2) 이번에 바꾼 기능을 실제 UI로 조작한다: <재생 버튼 클릭 등 구체적으로>. 3) 조작 전후 스크린샷을 .shots/ 폴더에 찍고, 찍을 때마다 반드시 read_file로 그 파일을 연다. read_file로 열지 않은 스크린샷은 근거로 쓰지 않는다. 4) read_file로 연 이미지를 기대한 모습 <수용 기준>과 비교한다. 항목별로 PASS 또는 FAIL을 보고할 때 근거로 삼은 파일 경로를 함께 쓰고, 보이지 않는 것은 보인다고 쓰지 마."
```

- 판단 기준은 스크린샷이다. `isContextLost()`나 화면의 글자만으로 판단하지 않는다.
- 수용 판단 전에 사람이 스크린샷을 직접 연다.
- `filename`은 항상 `.shots/`로 시작한다. 파일 이름을 주면 `--output-dir`이 적용되지 않고 Muse를 시작한 폴더 기준으로 저장된다.

## 6. goinfre가 지워졌을 때

증상은 `viewer/node_modules/.bin/tsc: no such file or directory` 같은 오류다. 리포 루트에서 실행한다.

```zsh
RT_ROOT="/goinfre/$USER/realtosim"
mkdir -p "$RT_ROOT/viewer-tools" "$RT_ROOT/shots"
cp viewer/package.json viewer/package-lock.json "$RT_ROOT/viewer-tools/"
(cd "$RT_ROOT/viewer-tools" && npm ci --ignore-scripts)
ln -sfn "$RT_ROOT/viewer-tools/node_modules" viewer/node_modules
ln -sfn "$RT_ROOT/shots" .shots
```

Playwright MCP는 4장의 설치 절차를 다시 실행한다.
