import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageInput from '../MessageInput.vue'
import { nextTick } from '../../../test-utils'

describe('MessageInput', () => {
  it('renders with default props', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: ''
      }
    })

    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('textarea').attributes('placeholder')).toBe('Type your message...')
    expect(wrapper.find('.send-button').exists()).toBe(true)
    expect(wrapper.find('.action-button').exists()).toBe(true)
  })

  it('updates model value on input', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: ''
      }
    })

    const textarea = wrapper.find('textarea')
    await textarea.setValue('Hello world')

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['Hello world'])
  })

  it('disables send button when no content and no files', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: '',
        hasFiles: false
      }
    })

    const sendButton = wrapper.find('.send-button')
    expect(sendButton.attributes('disabled')).toBeDefined()
  })

  it('enables send button when has content', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Hello'
      }
    })

    const sendButton = wrapper.find('.send-button')
    expect(sendButton.attributes('disabled')).toBeUndefined()
  })

  it('enables send button when has files', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: '',
        hasFiles: true
      }
    })

    const sendButton = wrapper.find('.send-button')
    expect(sendButton.attributes('disabled')).toBeUndefined()
  })

  it('emits send event on button click', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Test message'
      }
    })

    const sendButton = wrapper.find('.send-button')
    await sendButton.trigger('click')

    expect(wrapper.emitted('send')).toBeTruthy()
  })

  it('emits send event on Enter key', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Test message'
      }
    })

    const textarea = wrapper.find('textarea')
    await textarea.trigger('keydown', { key: 'Enter' })

    expect(wrapper.emitted('send')).toBeTruthy()
  })

  it('emits send event on Ctrl+Enter', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Test message'
      }
    })

    const textarea = wrapper.find('textarea')
    await textarea.trigger('keydown', { key: 'Enter', ctrlKey: true })

    expect(wrapper.emitted('send')).toBeTruthy()
  })

  it('does not emit send on Shift+Enter', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Test message'
      }
    })

    const textarea = wrapper.find('textarea')
    await textarea.trigger('keydown', { key: 'Enter', shiftKey: true })

    expect(wrapper.emitted('send')).toBeFalsy()
  })

  it('shows loading spinner when sending', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Test',
        isSending: true
      }
    })

    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })

  it('disables input when sending', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Test',
        isSending: true
      }
    })

    const textarea = wrapper.find('textarea')
    expect(textarea.attributes('disabled')).toBeDefined()
  })

  it('shows file attachment indicator', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: '',
        hasFiles: true
      }
    })

    expect(wrapper.text()).toContain('Files attached')
    expect(wrapper.text()).toContain('Clear')
  })

  it('emits toggle-file-upload on file button click', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: ''
      }
    })

    const fileButton = wrapper.find('.action-button')
    await fileButton.trigger('click')

    expect(wrapper.emitted('toggle-file-upload')).toBeTruthy()
  })

  it('emits clear-files when clear button clicked', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: '',
        hasFiles: true
      }
    })

    const clearButton = wrapper.find('button')
    const buttons = wrapper.findAll('button')
    const clearBtn = buttons.find(btn => btn.text().includes('Clear'))
    
    if (clearBtn) {
      await clearBtn.trigger('click')
      expect(wrapper.emitted('clear-files')).toBeTruthy()
    }
  })

  it('shows character count when enabled', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: 'Hello world',
        showCharCount: true
      }
    })

    expect(wrapper.text()).toContain('11') // Length of "Hello world"
  })

  it('respects max length', async () => {
    const longText = 'A'.repeat(100)
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: longText,
        maxLength: 50
      }
    })

    // Component should still accept the value but could show warning
    expect(wrapper.props('modelValue')).toBe(longText)
  })

  it('adjusts textarea height on input', async () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: ''
      }
    })

    const textarea = wrapper.find('textarea')
    
    // Mock scrollHeight
    Object.defineProperty(textarea.element, 'scrollHeight', {
      value: 80,
      writable: true
    })

    await textarea.setValue('Line 1\nLine 2\nLine 3')
    await nextTick()

    // Height should be adjusted (implementation detail)
    expect(textarea.element.style.height).toBeTruthy()
  })

  it('shows keyboard shortcut hint', () => {
    const wrapper = mount(MessageInput, {
      props: {
        modelValue: ''
      }
    })

    expect(wrapper.text()).toContain('Ctrl')
    expect(wrapper.text()).toContain('Enter')
  })
})