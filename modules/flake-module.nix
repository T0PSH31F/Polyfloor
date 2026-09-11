_: {
  # The primary, canonical NixOS module (company-as-tenant, SPEC §11).
  flake.nixosModules.default = import ./nixos/polyfloor.nix;

  # Legacy tower orchestration module (kept for backward compatibility).
  flake.nixosModules.polyfloor = import ./tower.nix;
}
