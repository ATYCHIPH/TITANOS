describe("TITANOS product workspace", () => {
  beforeEach(() => {
    cy.clearLocalStorage();
    cy.visit("http://localhost:8017/ui/index.html");
  });

  function loginAndOnboard() {
    cy.contains("TITANOS /one").should("be.visible");
    cy.get("#auth-email").type("owner@titanos.local");
    cy.get("#auth-password").type("password123");
    cy.contains("button", "Log in").click();
    cy.contains("What are you here to do?").should("be.visible");
    cy.contains("button", "Continue").click();
    cy.contains("How technical should TITANOS feel?").should("be.visible");
    cy.contains("button", "Continue").click();
    cy.contains("Choose visible tools").should("be.visible");
    cy.contains("button", "Continue").click();
    cy.contains("Connect an AI provider").should("be.visible");
    cy.contains("button", "Enter workspace").click();
  }

  it("protects the workspace behind auth and onboarding", () => {
    loginAndOnboard();
    cy.contains("Universal Workspace").should("be.visible");
    cy.contains("Ask anything").should("be.visible");
    cy.contains("Provider setup needed").should("be.visible");
  });

  it("toggles theme from the workspace shell", () => {
    loginAndOnboard();
    cy.get("html").should("have.attr", "data-theme", "dark");
    cy.get("#theme-toggle").click();
    cy.get("html").should("have.attr", "data-theme", "light");
  });

  it("runs a universal agent task with plan and result", () => {
    loginAndOnboard();
    cy.get("#command-input").type("Research competitors and make a report{enter}");
    cy.contains("Detected task").should("be.visible");
    cy.contains("Research").should("be.visible");
    cy.contains("Final result").should("be.visible");
  });
});
