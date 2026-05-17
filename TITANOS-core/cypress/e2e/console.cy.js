describe("TITANOS product workspace", () => {
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

  it("protects the workspace behind onboarding", () => {
    onboard();
    cy.contains("Operator Workspace").should("be.visible");
  });

  it("toggles theme from the workspace shell", () => {
    onboard();
    cy.get("html").should("have.attr", "data-theme", "dark");
    cy.get("#theme-toggle").click();
    cy.get("html").should("have.attr", "data-theme", "light");
  });

  it("runs a universal agent task with plan and result", () => {
    onboard();
    cy.get("textarea").type("Research competitors and make a report{enter}");
    cy.contains("Detected task").should("be.visible");
    cy.contains("Research").should("be.visible");
    cy.contains("Final result").should("be.visible");
  });
});
