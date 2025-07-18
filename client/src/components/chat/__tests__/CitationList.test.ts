import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CitationList from '../CitationList.vue'
import { createMockCitation } from '../../../test-utils'

describe('CitationList', () => {
  it('renders citations correctly', () => {
    const citations = [
      createMockCitation({
        id: '1',
        title: 'First Document',
        source: 'Source 1'
      }),
      createMockCitation({
        id: '2',
        title: 'Second Document',
        source: 'Source 2'
      })
    ]

    const wrapper = mount(CitationList, {
      props: { citations }
    })

    expect(wrapper.text()).toContain('Sources:')
    expect(wrapper.text()).toContain('First Document')
    expect(wrapper.text()).toContain('Second Document')
    expect(wrapper.text()).toContain('Source 1')
    expect(wrapper.text()).toContain('Source 2')
  })

  it('displays citation numbers correctly', () => {
    const citations = [
      createMockCitation({ id: '1', title: 'Doc 1' }),
      createMockCitation({ id: '2', title: 'Doc 2' }),
      createMockCitation({ id: '3', title: 'Doc 3' })
    ]

    const wrapper = mount(CitationList, {
      props: { citations }
    })

    const numbers = wrapper.findAll('.citation-number')
    expect(numbers).toHaveLength(3)
    expect(numbers[0].text()).toBe('1')
    expect(numbers[1].text()).toBe('2')
    expect(numbers[2].text()).toBe('3')
  })

  it('shows excerpts when available', () => {
    const citations = [
      createMockCitation({
        title: 'Document with excerpt',
        excerpt: 'This is a sample excerpt from the document.'
      })
    ]

    const wrapper = mount(CitationList, {
      props: { citations }
    })

    expect(wrapper.text()).toContain('This is a sample excerpt')
  })

  it('truncates long excerpts', () => {
    const longExcerpt = 'A'.repeat(150) // 150 characters
    const citations = [
      createMockCitation({
        title: 'Long excerpt document',
        excerpt: longExcerpt
      })
    ]

    const wrapper = mount(CitationList, {
      props: { citations }
    })

    const excerptElement = wrapper.find('.citation-excerpt')
    expect(excerptElement.text()).toContain('...')
    expect(excerptElement.text().length).toBeLessThan(longExcerpt.length)
  })

  it('emits citation-click event when citation is clicked', async () => {
    const citation = createMockCitation()
    const citations = [citation]

    const wrapper = mount(CitationList, {
      props: { citations }
    })

    const citationButton = wrapper.find('.citation-button')
    await citationButton.trigger('click')

    expect(wrapper.emitted('citation-click')).toBeTruthy()
    expect(wrapper.emitted('citation-click')?.[0]).toEqual([citation])
  })

  it('applies correct alignment classes', () => {
    const citations = [createMockCitation()]

    const leftWrapper = mount(CitationList, {
      props: { citations, align: 'left' }
    })

    const rightWrapper = mount(CitationList, {
      props: { citations, align: 'right' }
    })

    expect(leftWrapper.find('.ml-auto').exists()).toBe(false)
    expect(rightWrapper.find('.ml-auto').exists()).toBe(true)
  })

  it('handles empty citations array', () => {
    const wrapper = mount(CitationList, {
      props: { citations: [] }
    })

    expect(wrapper.text()).toContain('Sources:')
    expect(wrapper.findAll('.citation-button')).toHaveLength(0)
  })

  it('sets correct title attribute for accessibility', () => {
    const citation = createMockCitation({
      title: 'Test Document',
      excerpt: 'Test excerpt'
    })

    const wrapper = mount(CitationList, {
      props: { citations: [citation] }
    })

    const button = wrapper.find('.citation-button')
    expect(button.attributes('title')).toBe('Test excerpt')
  })

  it('falls back to title when no excerpt available', () => {
    const citation = createMockCitation({
      title: 'Test Document',
      excerpt: undefined
    })

    const wrapper = mount(CitationList, {
      props: { citations: [citation] }
    })

    const button = wrapper.find('.citation-button')
    expect(button.attributes('title')).toBe('Test Document')
  })
})