_: {
  flake.nixosModules.default = import ./nixos/polyfloor.nix;
  flake.nixosModules.polyfloor = import ./tower.nix;
  flake.nixosModules.floor-base = import ./floor-base.nix;
  flake.clan.modules = {
    polyfloor-core = ./tower.nix;
    floor-production = ./floors/templates/production.nix;
    floor-marketing = ./floors/templates/marketing.nix;
    floor-research = ./floors/templates/research.nix;
    floor-dev = ./floors/templates/dev.nix;
    floor-customer-svc = ./floors/templates/customer-service.nix;
  };
}

