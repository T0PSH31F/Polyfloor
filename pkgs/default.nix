{
  lib,
  stdenv,
  polyfloor-backend,
  makeWrapper,
}:

stdenv.mkDerivation {
  pname = "polyfloor";
  version = "0.1.0";

  src = ../.;

  nativeBuildInputs = [ makeWrapper ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin
    makeWrapper ${polyfloor-backend}/bin/polyfloor $out/bin/polyfloor \
      --set-default POLYFLOOR_HOST 127.0.0.1 \
      --set-default POLYFLOOR_PORT 8080
    runHook postInstall
  '';

  meta = with lib; {
    description = "Polyfloor — autonomous multi-company enterprise engine (backend daemon)";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
    mainProgram = "polyfloor";
  };
}
