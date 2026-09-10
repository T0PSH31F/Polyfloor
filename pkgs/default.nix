{ lib, stdenv, polyfloor-backend, polyfloor-frontend, makeWrapper }:

stdenv.mkDerivation {
  pname = "polyfloor";
  version = "0.1.0";

  src = ../.;

  nativeBuildInputs = [ makeWrapper ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin $out/share/polyfloor/frontend
    if [ -d "${polyfloor-frontend}" ]; then
      cp -r ${polyfloor-frontend}/* $out/share/polyfloor/frontend/
    fi
    makeWrapper ${polyfloor-backend}/bin/polyfloor $out/bin/polyfloor \
      --set POLYFLOOR_STATIC_DIR "$out/share/polyfloor/frontend"
    runHook postInstall
  '';

  meta = with lib; {
    description = "Polyfloor complete package (backend daemon + Svelte frontend)";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
    mainProgram = "polyfloor";
  };
}
