{ lib, python3Packages }:

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
    asyncpg
    sqlmodel
    aiosqlite
    alembic
    httpx
    sse-starlette
    structlog
  ];

  doCheck = false;

  meta = with lib; {
    description = "Polyfloor FastAPI backend service";
    homepage = "https://github.com/T0PSH31F/Polyfloor";
    license = licenses.mit;
    mainProgram = "polyfloor";
  };
}
