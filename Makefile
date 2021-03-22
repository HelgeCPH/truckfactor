PHONY: publish poetrypublish githubpublish

poetrypublish:
	poetry build
	poetry publish

githubpublish:
	echo ${GITHUB_API_KEY} > /tmp/git_token
	gh auth login --with-token < /tmp/git_token
	export VERSIONSTR=`poetry run python -c'import toml; fp = open("pyproject.toml"); print(toml.load(fp)["tool"]["poetry"]["version"]); fp.close()'`
	gh release create v${VERSIONSTR} './dist/truckfactor-${VERSIONSTR}.tar.gz'
	gh auth logout
	rm /tmp/git_token

publish: poetrypublish githubpublish