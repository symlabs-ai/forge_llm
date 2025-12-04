@auto-fallback
Feature: Auto Fallback Provider
  As a developer using ForgeLLMClient
  I want automatic fallback between providers
  So that my application is resilient when a provider fails

  Background:
    Given an auto-fallback provider with mock providers

  @primary-success
  Scenario: Primary provider succeeds
    Given the primary provider is healthy
    When I make a chat request
    Then the response should come from the primary provider
    And no fallback should occur

  @rate-limit-fallback
  Scenario: Fallback on rate limit error
    Given the primary provider fails with rate limit
    And the secondary provider is healthy
    When I make a chat request
    Then the response should come from the secondary provider
    And the fallback result should show 2 providers tried

  @timeout-fallback
  Scenario: Fallback on timeout error
    Given the primary provider fails with timeout
    And the secondary provider is healthy
    When I make a chat request
    Then the response should come from the secondary provider

  @auth-error-no-fallback
  Scenario: No fallback on authentication error
    Given the primary provider fails with authentication error
    And the secondary provider is healthy
    When I make a chat request
    Then the request should fail with AuthenticationError
    And the secondary provider should not be called

  @all-fail
  Scenario: All providers fail
    Given all providers fail with rate limit
    When I make a chat request
    Then the request should fail with AllProvidersFailedError
    And the error should contain provider errors

  @tracking
  Scenario: Tracking last provider used
    Given the primary provider fails with rate limit
    And the secondary provider is healthy
    When I make a chat request
    Then I can check which provider was used

  @streaming
  Scenario: Streaming with fallback
    Given the primary provider is healthy
    When I make a streaming chat request
    Then the stream should come from the primary provider

  @retry-before-fallback
  Scenario: Retry before fallback
    Given retry is enabled with 3 max retries
    And the primary provider fails 2 times then succeeds
    When I make a chat request
    Then the request should succeed from the primary provider
    And the primary provider should be called at least 3 times
    And no fallback should occur

  @retry-exhausted
  Scenario: Fallback after retry exhausted
    Given retry is enabled with 1 max retries
    And the primary provider always fails with rate limit
    And the secondary provider is healthy
    When I make a chat request
    Then the response should come from the secondary provider
    And the primary provider should be called at least 2 times
