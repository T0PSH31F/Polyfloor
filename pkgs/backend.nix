{
  lib,
  python3Packages,
}:

python3Packages.buildPythonPackage {
  pname = "polyfloor-backend";
  version = "0.1.0";
  pyproject = true;

  src = ../backend;

  build-system = with python3Packages; [
    hatchling
  ];

  dependencies = with python3Packages; [
    fastapi
    uvicorn
    pydantic
    pydantic-settings
    sqlmodel
    aiosqlite
    sqlalchemy
    httpx
    sse-starlette
    structlog
    prometheus-client
    pillow
  ];

  doCheck = false;

  meta = with lib; {
    description = "Polyfloor FastAPI backend — autonomous multi-company enterprise engine";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
    mainProgram = "polyfloor";
  };
}
