{
  description = "Polyfloor — Multi-floor AI company OS. Autonomous agent teams as isolated NixOS-native departments.";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    clan-core = {
      url = "git+https://git.clan.lol/clan/clan-core";
      inputs.nixpkgs.follows    = "nixpkgs";
      inputs.flake-parts.follows = "flake-parts";
    };
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs@{ flake-parts, clan-core, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
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

      perSystem = { pkgs, ... }: {
        formatter = pkgs.nixfmt-tree;
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            clan-core.packages.${pkgs.system}.clan-cli
            sops age postgresql python312 uv just
          ];
          shellHook = ''
            echo "🏢 Polyfloor dev shell"
            echo "  just check   — run all tests and lints"
            echo "  just db-migrate — apply DB migrations"
          '';
        };
      };
    };
}
