{ lib, buildNpmPackage }:

buildNpmPackage {
  pname = "polyfloor-frontend";
  version = "0.1.0";

  src = ../frontend;

  npmDepsHash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";

  buildPhase = ''
    runHook preBuild
    npm run build
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out
    cp -r build/* $out/ 2>/dev/null || cp -r .svelte-kit/output/* $out/ 2>/dev/null || cp -r dist/* $out/ 2>/dev/null || cp -r * $out/
    runHook postInstall
  '';

  meta = with lib; {
    description = "Polyfloor SvelteKit/Vite frontend UI";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
  };
}
