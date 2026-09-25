from app.markdown import article_markdown, content_hash, estimated_chunk_count
from app.scraper import _canonical_url


def test_markdown_keeps_heading_code_and_relative_link():
    result = article_markdown(
        "Install",
        "https://support.optisigns.com/hc/en-us/articles/1",
        '<h2>Setup</h2><p>See <a href="/hc/en-us/articles/2">next</a>.</p>'
        '<pre><code>npm run start</code></pre><nav>remove me</nav>',
    )
    assert "## Setup" in result
    assert "[next](/hc/en-us/articles/2)" in result
    assert "```" in result and "npm run start" in result
    assert "remove me" not in result
    assert "Article URL: https://support.optisigns.com/hc/en-us/articles/1" in result


def test_hash_is_stable_and_chunk_count_has_overlap():
    text = "word " * 450
    assert content_hash(text) == content_hash(text)
    assert estimated_chunk_count(text, 400, 40) == 2


def test_canonical_url_removes_fragment_and_trailing_slash():
    assert _canonical_url("https://example.com/article/#section") == "https://example.com/article"
