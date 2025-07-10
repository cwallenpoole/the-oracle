import unittest
import os
import sys
from unittest.mock import patch, MagicMock, ANY
import tempfile

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logic.ai_readers import (
    generate_text_with_llm, generate_iching_reading, generate_followup_reading,
    generate_runic_reading, analyze_fire_image, generate_flame_reading,
    USE_OLLAMA_FOR_TEXT, OLLAMA_MODEL, OLLAMA_HOST
)
from logic.iching import Reading, IChingHexagram, IChingAbout
from logic.runes import RunicReading, RuneElement
from models.user import User
from models.history import History


class TestAIReadersConfiguration(unittest.TestCase):
    """Test cases for AI readers configuration"""

    def test_configuration_defaults(self):
        """Test that configuration variables have expected defaults"""
        # These should be set from environment variables
        self.assertIsInstance(USE_OLLAMA_FOR_TEXT, bool)
        self.assertIsInstance(OLLAMA_MODEL, str)
        self.assertIsInstance(OLLAMA_HOST, str)


class TestGenerateTextWithLLM(unittest.TestCase):
    """Test cases for the main text generation function"""

    @patch('logic.ai_readers.ollama_client')
    def test_generate_text_with_ollama_success(self, mock_ollama):
        """Test successful text generation with Ollama"""
        with patch('logic.ai_readers.USE_OLLAMA_FOR_TEXT', True):
            mock_ollama.chat.return_value = {
                'message': {'content': 'Test response from Ollama'}
            }

            result = generate_text_with_llm(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt",
                temperature=0.7,
                max_tokens=100
            )

            self.assertEqual(result, 'Test response from Ollama')
            mock_ollama.chat.assert_called_once()

    @patch('logic.ai_readers.openai_client')
    @patch('logic.ai_readers.ollama_client')
    def test_generate_text_with_ollama_fallback(self, mock_ollama, mock_openai):
        """Test fallback to OpenAI when Ollama fails"""
        with patch('logic.ai_readers.USE_OLLAMA_FOR_TEXT', True):
            # Mock Ollama failure
            mock_ollama.chat.side_effect = Exception("Ollama connection failed")

            # Mock OpenAI success
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Test response from OpenAI"
            mock_openai.chat.completions.create.return_value = mock_response

            result = generate_text_with_llm(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt"
            )

            self.assertEqual(result, "Test response from OpenAI")
            mock_openai.chat.completions.create.assert_called_once()

    @patch('logic.ai_readers.openai_client')
    def test_generate_text_with_openai_direct(self, mock_openai):
        """Test direct OpenAI usage when configured"""
        with patch('logic.ai_readers.USE_OLLAMA_FOR_TEXT', False):
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Test response from OpenAI"
            mock_openai.chat.completions.create.return_value = mock_response

            result = generate_text_with_llm(
                system_prompt="Test system prompt",
                user_prompt="Test user prompt"
            )

            self.assertEqual(result, "Test response from OpenAI")
            mock_openai.chat.completions.create.assert_called_once()


class TestIChingReading(unittest.TestCase):
    """Test cases for I Ching reading generation"""

    def setUp(self):
        """Set up test data"""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()

        # Create mock user
        self.mock_user = MagicMock()
        self.mock_user.history.get_history_text_for_prompt.return_value = "Test history"

        # Create mock reading
        self.mock_reading = MagicMock()
        self.mock_reading.Current.Number = 31
        self.mock_reading.Current.Title = "Influence"
        self.mock_reading.Future = None
        self.mock_reading.has_transition.return_value = False
        self.mock_reading.__str__.return_value = "31 Influence"

    def tearDown(self):
        """Clean up after tests"""
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    @patch('logic.ai_readers.generate_text_with_llm')
    @patch('llm.memory.search')
    @patch('logic.iching.get_hgram_text')
    def test_generate_iching_reading_basic(self, mock_get_text, mock_search, mock_generate):
        """Test basic I Ching reading generation"""
        mock_search.return_value = [{'metadata': 'test metadata'}]
        mock_get_text.return_value = "Test hexagram text"
        mock_generate.return_value = "Test I Ching reading response"

        result = generate_iching_reading(
            question="Will I find love?",
            legacy_reading=self.mock_reading,
            user=self.mock_user,
            reading_id="test-reading-test_generate_iching_reading_basic"
        )

        self.assertEqual(result, "Test I Ching reading response")
        mock_generate.assert_called_once()

    @patch('logic.ai_readers.generate_text_with_llm')
    @patch('llm.memory.search')
    @patch('logic.iching.get_hgram_text')
    @patch('logic.ai_readers.LLMRequest')
    def test_generate_iching_reading_with_storage(self, mock_llm_request, mock_get_text, mock_search, mock_generate):
        """Test I Ching reading generation with LLM request storage"""
        mock_search.return_value = [{'metadata': 'test metadata'}]
        mock_get_text.return_value = "Test hexagram text"
        mock_generate.return_value = "Test I Ching reading response"

        # Set up the mock LLMRequest instance
        mock_llm_request_instance = MagicMock()
        mock_llm_request.return_value = mock_llm_request_instance

        result = generate_iching_reading(
            question="Will I find love?",
            legacy_reading=self.mock_reading,
            user=self.mock_user,
            reading_id="test-reading-123"
        )

        self.assertEqual(result, "Test I Ching reading response")

        # Verify LLMRequest was created with correct parameters
        mock_llm_request.assert_called_once_with(
            reading_id="test-reading-123",
            request_data=ANY,  # The prompt is dynamic, so we use ANY
            response_data="Test I Ching reading response",
            model_used=ANY,  # Model depends on USE_OLLAMA_FOR_TEXT
            request_type="initial"
        )
        mock_llm_request_instance.save.assert_called_once()


class TestRunicReading(unittest.TestCase):
    """Test cases for runic reading generation"""

    def setUp(self):
        """Set up test data"""
        # Create mock user
        self.mock_user = MagicMock()
        self.mock_user.history.get_history_text_for_prompt.return_value = "Test history"

        # Create mock runic reading
        self.mock_rune = MagicMock()
        self.mock_rune.symbol = "ᚠ"
        self.mock_rune.name = "Fehu"
        self.mock_rune.phonetic = "F"
        self.mock_rune.element = "Fire"
        self.mock_rune.deity = "Frey"
        self.mock_rune.is_reversed = False
        self.mock_rune.get_display_meaning.return_value = "Wealth, prosperity"

        self.mock_runic_reading = MagicMock()
        self.mock_runic_reading.runes = [self.mock_rune]
        self.mock_runic_reading.spread_type = "Single Rune"
        self.mock_runic_reading.spread_positions = {"position_1": "Present Situation"}

    @patch('logic.ai_readers.generate_text_with_llm')
    def test_generate_runic_reading_basic(self, mock_generate):
        """Test basic runic reading generation"""
        mock_generate.return_value = "Test runic reading response"

        result = generate_runic_reading(
            question="What should I focus on?",
            runic_reading=self.mock_runic_reading,
            user=self.mock_user
        )

        self.assertEqual(result, "Test runic reading response")
        mock_generate.assert_called_once()

        # Check that the prompt includes rune details
        call_args = mock_generate.call_args
        user_prompt = call_args[1]['user_prompt']
        self.assertIn("Fehu", user_prompt)
        self.assertIn("ᚠ", user_prompt)
        self.assertIn("Fire", user_prompt)

    @patch('logic.ai_readers.generate_text_with_llm')
    @patch('logic.ai_readers.LLMRequest')
    def test_generate_runic_reading_with_storage(self, mock_llm_request, mock_generate):
        """Test runic reading generation with LLM request storage"""
        mock_generate.return_value = "Test runic reading response"

        # Set up the mock LLMRequest instance
        mock_llm_request_instance = MagicMock()
        mock_llm_request.return_value = mock_llm_request_instance

        result = generate_runic_reading(
            question="What should I focus on?",
            runic_reading=self.mock_runic_reading,
            user=self.mock_user,
            reading_id="test-reading-456"
        )

        self.assertEqual(result, "Test runic reading response")

        # Verify LLMRequest was created with correct parameters
        mock_llm_request.assert_called_once_with(
            reading_id="test-reading-456",
            request_data=ANY,  # The prompt is dynamic, so we use ANY
            response_data="Test runic reading response",
            model_used=ANY,  # Model depends on USE_OLLAMA_FOR_TEXT
            request_type="initial"
        )
        mock_llm_request_instance.save.assert_called_once()


class TestFollowupReading(unittest.TestCase):
    """Test cases for follow-up reading generation"""

    def setUp(self):
        """Set up test data"""
        self.mock_user = MagicMock()
        self.mock_user.history.get_history_text_for_prompt.return_value = "Test history"

    @patch('logic.ai_readers.generate_text_with_llm')
    @patch('logic.ai_readers.LLMRequest')
    def test_generate_followup_reading(self, mock_llm_request, mock_generate):
        """Test followup reading generation"""
        mock_generate.return_value = "Test followup reading response"

        # Set up the mock LLMRequest instance
        mock_llm_request_instance = MagicMock()
        mock_llm_request.return_value = mock_llm_request_instance

        result = generate_followup_reading(
            question="Original question",
            followup_question="Followup question",
            original_response="Original response",
            original_request="Original request",
            user=self.mock_user,
            reading_id="test-reading-789"
        )

        self.assertEqual(result, "Test followup reading response")

        # Verify LLMRequest was created with correct parameters
        mock_llm_request.assert_called_once_with(
            reading_id="test-reading-789",
            request_data=ANY,  # The prompt is dynamic, so we use ANY
            response_data="Test followup reading response",
            model_used=ANY,  # Model depends on USE_OLLAMA_FOR_TEXT
            request_type="followup"
        )
        mock_llm_request_instance.save.assert_called_once()


class TestFireImageAnalysis(unittest.TestCase):
    """Test cases for fire image analysis"""

    @patch('logic.ai_readers.openai_client')
    def test_analyze_fire_image_success(self, mock_openai):
        """Test successful fire image analysis"""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Dancing figure, sacred tree, flowing water"
        mock_openai.chat.completions.create.return_value = mock_response

        result = analyze_fire_image("base64_image_data")

        self.assertEqual(result, "Dancing figure, sacred tree, flowing water")
        mock_openai.chat.completions.create.assert_called_once()

        # Verify that the image data was properly formatted
        call_args = mock_openai.chat.completions.create.call_args
        messages = call_args[1]['messages']
        image_content = messages[0]['content'][1]
        self.assertEqual(image_content['type'], 'image_url')
        self.assertIn('data:image/png;base64,', image_content['image_url']['url'])

    @patch('logic.ai_readers.openai_client')
    def test_analyze_fire_image_error(self, mock_openai):
        """Test fire image analysis error handling"""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        result = analyze_fire_image("base64_image_data")

        self.assertEqual(result, "Unable to analyze the fire image at this time.")


class TestFlameReading(unittest.TestCase):
    """Test cases for flame reading generation"""

    def setUp(self):
        """Set up test data"""
        self.mock_user = MagicMock()
        self.mock_user.history.get_history_text_for_prompt.return_value = "Test history"

    @patch('logic.ai_readers.generate_text_with_llm')
    def test_generate_flame_reading_basic(self, mock_generate):
        """Test basic flame reading generation"""
        mock_generate.return_value = "Test flame reading response"

        result = generate_flame_reading(
            vision_analysis="Dancing figure, sacred tree, flowing water",
            user=self.mock_user
        )

        self.assertEqual(result, "Test flame reading response")
        mock_generate.assert_called_once()

        # Check that the prompt includes the vision analysis
        call_args = mock_generate.call_args
        user_prompt = call_args[1]['user_prompt']
        self.assertIn("Dancing figure, sacred tree, flowing water", user_prompt)

    @patch('logic.ai_readers.generate_text_with_llm')
    @patch('logic.ai_readers.LLMRequest')
    def test_generate_flame_reading_with_storage(self, mock_llm_request, mock_generate):
        """Test flame reading generation with LLM request storage"""
        mock_generate.return_value = "Test flame reading response"

        # Set up the mock LLMRequest instance
        mock_llm_request_instance = MagicMock()
        mock_llm_request.return_value = mock_llm_request_instance

        result = generate_flame_reading(
            vision_analysis="Test vision analysis",
            user=self.mock_user,
            reading_id="test-reading-012"
        )

        self.assertEqual(result, "Test flame reading response")

        # Verify LLMRequest was created with correct parameters
        mock_llm_request.assert_called_once_with(
            reading_id="test-reading-012",
            request_data=ANY,  # The prompt is dynamic, so we use ANY
            response_data="Test flame reading response",
            model_used=ANY,  # Model depends on USE_OLLAMA_FOR_TEXT
            request_type="initial"
        )
        mock_llm_request_instance.save.assert_called_once()


if __name__ == '__main__':
    unittest.main()
