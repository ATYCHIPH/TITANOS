describe("TITANOS production flows", () => {
  beforeEach(() => {
    cy.clearLocalStorage();
    cy.visit("http://localhost:8017/ui/index.html");
    cy.contains("button", "Next").click();
    cy.contains("button", "Next").click();
    cy.contains("button", "Complete Setup").click();
  });

  it("switches workspace and technical level", () => {
    cy.get("#workspace-switcher").select("coding");
    cy.contains("Coding Workspace").should("be.visible");
    cy.get("#level-switcher").select("developer");
    cy.contains("Terminal").should("be.visible");
    cy.contains("Git and Diffs").should("be.visible");
  });

  it("saves and tests a local provider without exposing a key", () => {
    cy.contains("button", "API Keys").click();
    cy.get('[data-provider-form="local"] input[name="baseUrl"]').clear().type("localhost:11434");
    cy.get('[data-provider-form="local"] input[name="model"]').clear().type("llama3.3");
    cy.get('[data-provider-form="local"] button[type="submit"]').click();
    cy.contains("Local endpoint").should("be.visible");
    cy.contains("Connected").should("be.visible");
    cy.contains("Saved key: Not saved").should("be.visible");
  });

  it("requires approval for sensitive agent actions", () => {
    cy.get("#command-input").type("Deploy code and send email to the team{enter}");
    cy.contains("Approval required").should("be.visible");
    cy.contains("send email").should("be.visible");
    cy.contains("button", "Approve and continue").click();
    cy.contains("Final result").should("be.visible");
  });

  it("opens settings, permissions, and usage routes", () => {
    cy.contains("button", "Settings").click();
    cy.contains("Workspace Settings").should("be.visible");
    cy.contains("button", "Permissions").click();
    cy.contains("Tool Permissions").should("be.visible");
    cy.contains("button", "Usage").click();
    cy.contains("Usage and Billing").should("be.visible");
  });
});
