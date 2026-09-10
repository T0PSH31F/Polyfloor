# Customer Service floor template
# Ticket handling, support workflows, customer analytics
{ lib, ... }:
with lib;
{
  tower.floors.customer-service = {
    enable = true;
    displayName = "Customer Service";
    email = "support@polyfloor.local";
    orgName = "customer-service";
    timezone = "America/Los_Angeles";
    targetMachine = "luffy";
    dbSchema = "floor_customer_service";
    mcps = [ ];
    template = "customer-service";

    roles = {
      manager = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 8192;
        description = "Manages support team, handles escalations, sets priorities";
      };
      agent = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Handles customer tickets, provides responses";
      };
      analyst = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Analyzes support metrics, identifies trends and issues";
      };
    };

    dailyBudgetUSD = 0.0;
    persistPaths = [ "outputs" "sessions" "sprint-board" ];
  };
}
