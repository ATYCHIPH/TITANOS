class Titanos < Formula
  desc "TITANOS agentic framework backend"
  homepage "https://github.com/your-org/TITANOS"
  url "https://github.com/your-org/TITANOS/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_SHA256"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/titanos", "--help"
  end
end
