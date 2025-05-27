"""Basic tests for Articles to Anki package."""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

# Import your modules (these will need to be updated with proper package imports)
try:
    from articles_to_anki import Article, ExportCards, __version__
    from articles_to_anki.text_utils import normalize_text, calculate_similarity
except ImportError:
    # Fallback for when running tests before package restructure
    import sys
    sys.path.insert(0, '.')
    from articles import Article
    from export_cards import ExportCards
    from text_utils import normalize_text, calculate_similarity
    __version__ = "0.1.0"


class TestVersion:
    """Test version information."""

    def test_version_exists(self):
        """Test that version is defined."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__.split('.')) == 3  # major.minor.patch


class TestArticle:
    """Test Article class functionality."""

    def test_article_init_with_url(self):
        """Test Article initialization with URL."""
        url = "https://example.com/article"
        article = Article(url=url)
        assert article.url == url
        assert article.file_path is None
        assert article.identifier == url

    def test_article_init_with_file(self):
        """Test Article initialization with file path."""
        file_path = "/path/to/file.pdf"
        article = Article(file_path=file_path)
        assert article.file_path == file_path
        assert article.url is None
        assert article.identifier == "file.pdf"

    def test_article_init_no_params(self):
        """Test Article initialization without parameters raises error."""
        article = Article()
        with pytest.raises(ValueError):
            _ = article.identifier

    def test_content_hash_generation(self):
        """Test content hash generation."""
        article = Article(url="https://example.com")
        article.title = "Test Title"
        article.text = "Test content"
        article._generate_content_hash()

        assert article.content_hash is not None
        assert len(article.content_hash) == 64  # SHA256 hex length

    @patch('articles_to_anki.articles.requests.get')
    def test_fetch_from_url_success(self, mock_get):
        """Test successful URL fetching."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '<html><body><h1>Test Title</h1><p>Test content</p></body></html>'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        article = Article(url="https://example.com/test")
        # We can't easily test the full fetch_content without mocking more,
        # but we can test that the Article object is properly set up
        assert article.url == "https://example.com/test"


class TestTextUtils:
    """Test text utility functions."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        text = "This is a TEST with punctuation!"
        normalized = normalize_text(text)

        # Should be lowercase and have punctuation removed
        assert normalized.islower()
        assert "!" not in normalized
        assert "test" in normalized

    def test_normalize_text_empty(self):
        """Test normalization of empty text."""
        assert normalize_text("") == ""
        assert normalize_text(None) == ""

    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical texts."""
        text1 = "This is a test sentence"
        text2 = "This is a test sentence"

        similarity = calculate_similarity(text1, text2)
        assert similarity == 1.0

    def test_calculate_similarity_different(self):
        """Test similarity calculation for different texts."""
        text1 = "This is about cats"
        text2 = "This is about dogs"

        similarity = calculate_similarity(text1, text2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.0  # Should have some similarity due to common words

    def test_calculate_similarity_empty(self):
        """Test similarity calculation for empty texts."""
        assert calculate_similarity("", "test") == 0.0
        assert calculate_similarity("test", "") == 0.0
        assert calculate_similarity("", "") == 0.0


class TestExportCards:
    """Test ExportCards functionality."""

    def test_export_cards_init(self):
        """Test ExportCards initialization."""
        cloze_cards = ["{{c1::test}} card"]
        basic_cards = ["Question ; Answer ;"]

        exporter = ExportCards(
            cloze_cards=cloze_cards,
            basic_cards=basic_cards,
            title="Test Article",
            deck="Test Deck"
        )

        assert exporter.cloze_cards == cloze_cards
        assert exporter.basic_cards == basic_cards
        assert exporter.title == "Test Article"
        assert exporter.deck == "Test Deck"

    def test_export_to_file(self):
        """Test exporting cards to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for test
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)

                exporter = ExportCards(
                    cloze_cards=["{{c1::test}} card ; ;"],
                    basic_cards=["Question ; Answer ;"],
                    title="Test Article",
                    deck="Test Deck",
                    to_file=True,
                    skip_duplicates=False  # Disable duplicate checking for test
                )

                exporter.export()

                # Check that exported_cards directory was created
                assert os.path.exists("exported_cards")

                # Check that files were created
                files = os.listdir("exported_cards")
                cloze_files = [f for f in files if "cloze" in f]
                basic_files = [f for f in files if "basic" in f]

                assert len(cloze_files) > 0
                assert len(basic_files) > 0

            finally:
                os.chdir(original_cwd)


class TestIntegration:
    """Integration tests."""

    def test_package_imports(self):
        """Test that all main components can be imported."""
        # This test ensures the package structure is correct
        try:
            from articles_to_anki import Article, ExportCards
            from articles_to_anki.text_utils import normalize_text
            from articles_to_anki.config import OPENAI_API_KEY
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_cli_entry_points(self):
        """Test that CLI entry points are properly defined."""
        # This would be tested in a real environment with the installed package
        # For now, just test that the main functions exist
        try:
            from articles_to_anki.cli import main as cli_main
            from articles_to_anki.setup_app import main as setup_main
            from articles_to_anki.fix_nltk import fix_nltk_issues

            # Just check they're callable
            assert callable(cli_main)
            assert callable(setup_main)
            assert callable(fix_nltk_issues)
        except ImportError as e:
            pytest.fail(f"CLI entry point import failed: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
