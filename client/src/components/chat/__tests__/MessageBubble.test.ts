import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '../MessageBubble.vue'
import CitationList from '../CitationList.vue'
import { createMockMessage, createMockCitation } from '../../../test-utils'

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    const message = createMockMessage({
      role: 'user',
      content: 'Hello, how are you?'
    })

    const wrapper = mount(MessageBubble, {
      props: { message }
    })

    expect(wrapper.text()).toContain('Hello, how are you?')
    expect(wrapper.find('.justify-end').exists()).toBe(true) // User messages align right
    expect(wrapper.find('.bg-blue-500').exists()).toBe(true) // User message styling
  })

  it('renders assistant message with markdown', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: '**Bold text** and `code`'
    })

    const wrapper = mount(MessageBubble, {
      props: { message }
    })

    expect(wrapper.find('.justify-start').exists()).toBe(true) // Assistant messages align left
    expect(wrapper.find('.bg-gray-100').exists()).toBe(true) // Assistant message styling
    expect(wrapper.find('.prose').exists()).toBe(true) // Markdown prose styling
  })

  it('displays citations when present', () => {
    const citations = [createMockCitation()]
    const message = createMockMessage({
      role: 'assistant',
      content: 'Here is some information [1]',
      citations
    })

    const wrapper = mount(MessageBubble, {
      props: { message },
      global: {
        components: { CitationList }
      }
    })

    expect(wrapper.findComponent(CitationList).exists()).toBe(true)
    expect(wrapper.findComponent(CitationList).props('citations')).toEqual(citations)
  })

  it('shows streaming indicator when streaming', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Partial response...'
    })

    const wrapper = mount(MessageBubble, {
      props: { 
        message,
        isStreaming: true
      }
    })

    expect(wrapper.text()).toContain('AI is typing...')
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
  })

  it('formats timestamp correctly', () => {
    const now = new Date()
    const message = createMockMessage({
      timestamp: now
    })

    const wrapper = mount(MessageBubble, {
      props: { message }
    })

    expect(wrapper.text()).toContain('Just now')
  })

  it('emits citation-click event', async () => {
    const citation = createMockCitation()
    const message = createMockMessage({
      role: 'assistant',
      citations: [citation]
    })

    const wrapper = mount(MessageBubble, {
      props: { message },
      global: {
        components: { CitationList }
      }
    })

    const citationList = wrapper.findComponent(CitationList)
    await citationList.vm.$emit('citation-click', citation)

    expect(wrapper.emitted('citation-click')).toBeTruthy()
    expect(wrapper.emitted('citation-click')?.[0]).toEqual([citation])
  })

  it('handles markdown parsing errors gracefully', () => {
    const message = createMockMessage({
      role: 'assistant',
      content: 'Normal text content'
    })

    // Mock marked.parse to throw an error
    vi.doMock('marked', () => ({
      marked: {
        parse: vi.fn().mockImplementation(() => {
          throw new Error('Parsing error')
        }),
        setOptions: vi.fn()
      }
    }))

    const wrapper = mount(MessageBubble, {
      props: { message }
    })

    // Should fallback to wrapped content
    expect(wrapper.html()).toContain('Normal text content')
  })

  it('applies correct alignment classes', () => {
    const userMessage = createMockMessage({ role: 'user' })
    const assistantMessage = createMockMessage({ role: 'assistant' })

    const userWrapper = mount(MessageBubble, {
      props: { message: userMessage }
    })

    const assistantWrapper = mount(MessageBubble, {
      props: { message: assistantMessage }
    })

    expect(userWrapper.find('.justify-end').exists()).toBe(true)
    expect(assistantWrapper.find('.justify-start').exists()).toBe(true)
  })
})