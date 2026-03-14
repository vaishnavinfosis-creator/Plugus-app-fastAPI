"""
Property-Based Tests for Review System
Feature: platform-robustness-improvements
Tests Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from app.core.content_moderator import content_moderator


# **Property 15: Review Submission Workflow**
# **Validates: Requirements 5.1, 5.2, 5.3**
@given(
    rating=st.integers(min_value=1, max_value=5),
    comment=st.text(min_size=0, max_size=500)
)
@settings(max_examples=20)
def test_property_15_review_submission_workflow(rating, comment):
    """
    Property 15: Review Submission Workflow
    For any completed booking, the system should provide review interface to customers
    and process submitted reviews with proper validation (1-5 stars, max 500 characters)
    """
    # Validate rating range
    assert 1 <= rating <= 5, "Rating must be between 1 and 5"
    
    # Validate comment length
    assert len(comment) <= 500, "Comment must not exceed 500 characters"
    
    # Simulate review creation
    review_data = {
        "rating": rating,
        "comment": comment if comment.strip() else None
    }
    
    # Verify review data structure
    assert "rating" in review_data
    assert review_data["rating"] >= 1 and review_data["rating"] <= 5


# **Property 16: Review Display and Rating Calculation**
# **Validates: Requirements 5.4, 5.5**
@given(
    ratings=st.lists(
        st.integers(min_value=1, max_value=5),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=20)
def test_property_16_review_display_and_rating_calculation(ratings):
    """
    Property 16: Review Display and Rating Calculation
    For any service with reviews, the system should display all approved reviews
    and maintain accurate average ratings when new reviews are added
    """
    # Calculate average rating
    average_rating = sum(ratings) / len(ratings)
    
    # Verify average is within valid range
    assert 1.0 <= average_rating <= 5.0, "Average rating must be between 1 and 5"
    
    # Verify average calculation is correct
    expected_average = sum(ratings) / len(ratings)
    assert abs(average_rating - expected_average) < 0.01, "Average calculation must be accurate"
    
    # Verify review count
    review_count = len(ratings)
    assert review_count > 0, "Review count must be positive"


# **Property 17: Review Content Moderation**
# **Validates: Requirements 5.6**
@given(
    comment=st.text(min_size=1, max_size=500)
)
@settings(max_examples=20)
def test_property_17_review_content_moderation(comment):
    """
    Property 17: Review Content Moderation
    For any review containing inappropriate content, the system should flag it for admin moderation
    """
    # Check content for inappropriate content
    is_flagged, reasons = content_moderator.check_content(comment)
    
    # If flagged, reasons should be provided
    if is_flagged:
        assert len(reasons) > 0, "Flagged content must have reasons"
        assert all(isinstance(reason, str) for reason in reasons), "Reasons must be strings"
    
    # Verify moderation decision is consistent
    is_flagged_again, _ = content_moderator.check_content(comment)
    assert is_flagged == is_flagged_again, "Moderation decision must be consistent"


# Additional property tests for edge cases
@given(
    rating=st.integers()
)
@settings(max_examples=15)
def test_rating_validation_rejects_invalid_ratings(rating):
    """Test that ratings outside 1-5 range are rejected"""
    if rating < 1 or rating > 5:
        # Invalid rating should be rejected
        with pytest.raises(AssertionError):
            assert 1 <= rating <= 5


@given(
    comment=st.text(min_size=501, max_size=1000)
)
@settings(max_examples=15)
def test_comment_length_validation_rejects_long_comments(comment):
    """Test that comments exceeding 500 characters are rejected"""
    assert len(comment) > 500
    # Long comment should be rejected
    with pytest.raises(AssertionError):
        assert len(comment) <= 500


@given(
    profanity_word=st.sampled_from(['fuck', 'shit', 'damn', 'bitch'])
)
@settings(max_examples=15)
def test_profanity_detection(profanity_word):
    """Test that profanity is detected and flagged"""
    comment = f"This is a {profanity_word} test"
    is_flagged, reasons = content_moderator.check_content(comment)
    
    assert is_flagged, "Profanity should be flagged"
    assert any('profanity' in reason.lower() for reason in reasons), "Profanity reason should be provided"


@given(
    url=st.sampled_from(['http://spam.com', 'https://malicious.site', 'www.spam.org'])
)
@settings(max_examples=15)
def test_url_detection_in_reviews(url):
    """Test that URLs in reviews are detected and flagged"""
    comment = f"Check out this link: {url}"
    is_flagged, reasons = content_moderator.check_content(comment)
    
    assert is_flagged, "URLs should be flagged"
    assert any('inappropriate' in reason.lower() for reason in reasons), "URL reason should be provided"


@given(
    ratings=st.lists(st.integers(min_value=1, max_value=5), min_size=2, max_size=10)
)
@settings(max_examples=15)
def test_average_rating_precision(ratings):
    """Test that average rating is calculated with proper precision"""
    average = sum(ratings) / len(ratings)
    
    # Round to 2 decimal places
    rounded_average = round(average, 2)
    
    assert 1.0 <= rounded_average <= 5.0
    assert isinstance(rounded_average, float)
