{ lib
, stdenv
, polyfloor-backend
, polyfloor-frontend ? null
, makeWrapper
,
}:

stdenv.mkDerivation {
  pname =
    if polyfloor-frontend != null then
      "polyfloor-full"
    else
      "polyfloor";
  version = "0.1.0";

  src = ../.;

  nativeBuildInputs = [ makeWrapper ];

  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin
    ${lib.optionalString (polyfloor-frontend != null) ''
      mkdir -p $out/share/polyfloor/frontend
      cp -r ${polyfloor-frontend}/* $out/share/polyfloor/frontend/
    ''}
    makeWrapper ${polyfloor-backend}/bin/polyfloor $out/bin/polyfloor \
      ${lib.optionalString (polyfloor-frontend != null) ''
        --set-default POLYFLOOR_STATIC_DIR "$out/share/polyfloor/frontend"
      ''}
    runHook postInstall
  '';

  meta = with lib; {
    description =
      if polyfloor-frontend != null then
        "Polyfloor — backend + frontend SPA bundle"
      else
        "Polyfloor — backend daemon (API + SPA-if-staticDir-set)";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
    mainProgram = "polyfloor";
  };
}
