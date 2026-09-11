{ lib
, stdenv
, polyfloor-backend
, makeWrapper
,
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
    # config.py defaults to 127.0.0.1:8001; do not override here so `nix run`
    # matches the documented port. Set POLYFLOOR_STATIC_DIR to serve the SPA.
    makeWrapper ${polyfloor-backend}/bin/polyfloor $out/bin/polyfloor
    runHook postInstall
  '';

  meta = with lib; {
    description = "Polyfloor — autonomous multi-company enterprise engine (backend daemon)";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
    mainProgram = "polyfloor";
  };
}
