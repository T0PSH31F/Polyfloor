{
  description = "Polyfloor — Multi-floor AI company OS. Autonomous agent teams as isolated NixOS-native departments.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    git-hooks-nix = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    clan-core = {
      url = "git+https://git.clan.lol/clan/clan-core";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-parts.follows = "flake-parts";
    };
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs@{ flake-parts, clan-core, treefmt-nix, git-hooks-nix, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        treefmt-nix.flakeModule
        git-hooks-nix.flakeModule
        clan-core.flakeModules.default
        ./modules/flake-module.nix
      ];

      systems = [ "x86_64-linux" "aarch64-linux" ];

      clan = {
        specialArgs = { inherit inputs; };
        pkgsForSystem = system: import inputs.nixpkgs {
          localSystem = system;
          config.allowUnfree = true;
        };
      };

      perSystem = { config, pkgs, self', ... }: {
        treefmt = {
          projectRootFile = "flake.nix";
          programs.nixpkgs-fmt.enable = true;
          programs.deadnix.enable = true;
          programs.statix.enable = true;
          programs.prettier.enable = true;
          programs.ruff-format.enable = true;
          programs.ruff-check.enable = true;
          programs.mdformat.enable = true;
        };

        # NOTE: we do NOT enable the git-hooks treefmt hook here. It uses a
        # different treefmt version than treefmt-nix's `checks.treefmt` and the
        # two fight over .md formatting. `checks.treefmt` is the single source
        # of truth for formatting.
        pre-commit = {
          check.enable = true;
        };

        packages = {
          backend = pkgs.callPackage ./pkgs/backend.nix { };
          frontend = pkgs.callPackage ./pkgs/frontend.nix { };
          default = pkgs.callPackage ./pkgs/default.nix {
            polyfloor-backend = self'.packages.backend;
          };
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ config.pre-commit.devShell ];
          packages = with pkgs; [
            nodejs_22
            pnpm
            python312
            uv
            python312Packages.fastapi
            python312Packages.uvicorn
            python312Packages.pytest
            python312Packages.ruff
            python312Packages.mypy
            just
            sqlite
            curl
            jq
            sops
            age
          ];
          shellHook = ''
            ${config.pre-commit.installationScript}
            echo "🏢 Polyfloor dev shell"
            echo "  just dev     — run local dev servers"
            echo "  just check   — run all tests and lints"
            echo "  just fmt     — format code"
          '';
        };

        # NOTE: `frontend` is intentionally excluded from checks — its
        # buildNpmPackage npmDepsHash must be populated first (see
        # pkgs/frontend.nix). `nix flake check` builds checks, so we only list
        # derivations that build from source without a network fetch.
        checks = {
          backend = self'.packages.backend;
          default = self'.packages.default;
        };
      };
    };
}
