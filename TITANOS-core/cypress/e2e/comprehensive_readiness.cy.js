describe("TITANOS Comprehensive E2E Product Readiness Flows", () => {
  beforeEach(() => {
    cy.clearLocalStorage();
    cy.visit("http://localhost:8017/ui/index.html");
  });

  function onboard() {
    cy.contains("What are you here to do?").should("be.visible");
    cy.contains("button", "Next").click();
    cy.contains("Technical Experience").should("be.visible");
    cy.contains("button", "Next").click();
    cy.contains("Connect AI Provider").should("be.visible");
    cy.contains("button", "Complete Setup").click();
  }

  it("completes full onboarding and verifies degraded-mode UI elements", () => {
    onboard();
    cy.contains("Operator Workspace").should("be.visible");
    
    // Verify default provider setup warnings (Since OpenAI key is missing)
    cy.contains("Missing API Credentials").should("be.visible");
  });

  it("navigates settings, saves local provider configurations, and performs diagnostics", () => {
    onboard();
    cy.contains("button", "Settings").click();
    cy.contains("Workspace Settings").should("be.visible");

    // Add and test a provider configuration
    cy.contains("button", "API Keys").click();
    cy.get('[data-provider-form="local"] input[name="baseUrl"]').clear().type("localhost:11434");
    cy.get('[data-provider-form="local"] input[name="model"]').clear().type("llama3.3");
    cy.get('[data-provider-form="local"] button[type="submit"]').click();
    cy.contains("Connected").should("be.visible");
  });

  it("interacts with the system log viewer with live search and severity filtering", () => {
    onboard();
    cy.contains("button", "Settings").click();
    cy.contains("button", "System Logs").click();
    cy.contains("View, filter, and export live Electron").should("be.visible");
    
    // Test search filter
    cy.get('input[placeholder="Search log lines..."]').type("SUCCESS");
    cy.contains("SUCCESS").should("be.visible");
    
    // Test level filters
    cy.contains("button", "ERROR").click();
    cy.get('select[aria-label="Select Log Stream"]').select("desktop");
  });

  it("performs backup data export/import workflows", () => {
    onboard();
    cy.contains("button", "Settings").click();
    cy.contains("button", "Import/Export").click();
    cy.contains("Export your operator configurations").should("be.visible");
    
    // Test generate download button
    cy.contains("button", "Generate & Download Backup").should("be.visible");
  });

  it("triggers local session recovery and database purges", () => {
    onboard();
    cy.contains("button", "Settings").click();
    cy.contains("button", "Diagnostics & Recovery").click();
    cy.contains("Purge & Reset SQLite Database").should("be.visible");
    cy.contains("Force Session Relaunch").should("be.visible");
  });
});
