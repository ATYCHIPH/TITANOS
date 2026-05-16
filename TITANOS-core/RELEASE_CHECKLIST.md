# TITANOS Release Checklist

Follow these steps before every production release.

## 1. Versioning
- [ ] Increment version in `pyproject.toml`.
- [ ] Increment version in `titanos/config/settings.py`.
- [ ] Update version in `ui/index.html`.
- [ ] Create a git tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.

## 2. Testing & Quality
- [x] Run full build check: `python scripts/run.py build`.
- [x] Run all unit tests: `python scripts/run.py test`.
- [x] Run API tests: `python scripts/run.py api-test`.
- [ ] Run command approval flow tests.
- [ ] Run file write/edit safety tests.
- [ ] Run system health check: `python scripts/run.py doctor`.
- [ ] Run UI tests: `python scripts/run.py ui-test` (or skip with reason if node_modules missing).
- [ ] Verify CI passes on all platforms (Windows, Ubuntu, macOS).
- [ ] Manual smoke test of the Operator Console.
- [ ] Check for any hardcoded keys or local paths in the source.
- [ ] Ensure no required dependency is missing for server import.

## 3. Documentation
- [ ] Update `README.md` with new features or changes.
- [ ] Update `MIGRATION.md` if any body systems were grafted.
- [ ] Update `BUILD_LOG.md` with the final release build status.

## 4. Packaging
- [ ] Build Python wheel: `python packaging/wheel_build.py`.
- [ ] Build standalone executable: `python packaging/exe_build.py`.
- [ ] Verify the executable runs on a clean machine without Python.

## 5. Security
- [ ] Run a secret scanner (e.g., `trufflehog`) on the repository.
- [ ] Review `SECURITY_REVIEW.md` for any new risks introduced.

## 6. Distribution
- [ ] Push tags to GitHub: `git push origin --tags`.
- [ ] Upload wheel and executable to GitHub Release.
- [ ] Publish to PyPI (if applicable): `twine upload dist/*`.
