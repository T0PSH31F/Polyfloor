{ lib
, buildNpmPackage
,
}:

buildNpmPackage {
  pname = "polyfloor-frontend";
  version = "0.1.0";

  src = ../frontend;

  # NOTE: regenerate with `nix build .#frontend` after changing package-lock.json,
  # then `prefetch-npm-deps ./frontend/package-lock.json` and paste the hash here.
  npmDepsHash = lib.fakeHash;

  buildPhase = ''
    runHook preBuild
    npm run build
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p $out
    cp -r build/* $out/
    runHook postInstall
  '';

  meta = with lib; {
    description = "Polyfloor SvelteKit GBA/DS dual-screen frontend";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
  };
}
