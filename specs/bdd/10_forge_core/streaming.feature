@streaming
Feature: Enhanced Streaming Support
  As a developer using ForgeLLMClient
  I want typed streaming events
  So that I can handle different event types appropriately

  Background:
    Given a client with mock provider for streaming

  @typed-events
  Scenario: Receive typed content events
    When I stream a message "Hello"
    Then I should receive StreamEvent objects
    And the events should have type CONTENT

  @aggregation
  Scenario: Aggregate streaming content
    Given a stream aggregator
    When I receive content events "Hello" and " World"
    Then the aggregated content should be "Hello World"

  @tool-call-streaming
  Scenario: Stream tool call events
    Given a mock stream with tool calls
    When I stream and collect events
    Then I should receive TOOL_CALL_START event
    And I should receive TOOL_CALL_DELTA events
    And I should receive TOOL_CALL_DONE event

  @aggregator-tool-calls
  Scenario: Aggregate tool calls from stream
    Given a stream aggregator
    When I receive tool call events for get_weather with arguments
    Then the aggregator should have 1 tool call
    And the tool call name should be "get_weather"

  @done-event
  Scenario: Receive done event at end of stream
    When I stream a complete message
    Then the last event should be DONE
    And the finish_reason should be "stop"

  @error-event
  Scenario: Handle stream error events
    Given a mock stream that errors
    When I stream and collect events
    Then I should receive an ERROR event

  @mixed-content
  Scenario: Handle mixed content and tool calls
    Given a mock stream with content and tool calls
    When I stream and collect events
    Then I should receive both CONTENT and TOOL_CALL events
    And the aggregator should have content and tool calls
