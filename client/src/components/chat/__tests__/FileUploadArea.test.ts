import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FileUploadArea from '../FileUploadArea.vue'
import { createMockFile, createMockFileObject, createFileDropEvent } from '../../../test-utils'

describe('FileUploadArea', () => {
  it('renders upload area correctly', () => {
    const wrapper = mount(FileUploadArea, {
      props: {
        files: []
      }
    })

    expect(wrapper.text()).toContain('Click to upload')
    expect(wrapper.text()).toContain('or drag and drop')
    expect(wrapper.text()).toContain('Images, logs, documents')
  })

  it('displays uploaded files', () => {
    const files = [
      createMockFile({
        name: 'test.txt',
        size: 1024,
        status: 'completed'
      }),
      createMockFile({
        name: 'image.png',
        size: 2048,
        status: 'pending'
      })
    ]

    const wrapper = mount(FileUploadArea, {
      props: { files }
    })

    expect(wrapper.text()).toContain('Attached Files (2)')
    expect(wrapper.text()).toContain('test.txt')
    expect(wrapper.text()).toContain('image.png')
    expect(wrapper.text()).toContain('1 KB')
    expect(wrapper.text()).toContain('2 KB')
  })

  it('shows progress bar for uploading files', () => {
    const files = [
      createMockFile({
        status: 'uploading',
        progress: 50
      })
    ]

    const wrapper = mount(FileUploadArea, {
      props: { files }
    })

    expect(wrapper.text()).toContain('Uploading... 50%')
    expect(wrapper.find('.bg-blue-500').exists()).toBe(true) // Progress bar
  })

  it('shows success status for completed files', () => {
    const files = [
      createMockFile({
        status: 'completed'
      })
    ]

    const wrapper = mount(FileUploadArea, {
      props: { files }
    })

    expect(wrapper.text()).toContain('Upload complete')
  })

  it('shows error status for failed files', () => {
    const files = [
      createMockFile({
        status: 'error',
        error: 'Upload failed'
      })
    ]

    const wrapper = mount(FileUploadArea, {
      props: { files }
    })

    expect(wrapper.text()).toContain('Upload failed')
  })

  it('emits file-remove when remove button clicked', async () => {
    const files = [createMockFile({ id: 'test-file-1' })]

    const wrapper = mount(FileUploadArea, {
      props: { files }
    })

    const removeButton = wrapper.find('.remove-button')
    await removeButton.trigger('click')

    expect(wrapper.emitted('file-remove')).toBeTruthy()
    expect(wrapper.emitted('file-remove')?.[0]).toEqual(['test-file-1'])
  })

  it('triggers file input on click', async () => {
    const wrapper = mount(FileUploadArea, {
      props: { files: [] }
    })

    const fileInput = wrapper.find('input[type="file"]')
    const clickSpy = vi.spyOn(fileInput.element, 'click')

    const dropZone = wrapper.find('.border-dashed')
    await dropZone.trigger('click')

    expect(clickSpy).toHaveBeenCalled()
  })

  it('handles file selection from input', async () => {
    const wrapper = mount(FileUploadArea, {
      props: { files: [] }
    })

    const file = createMockFileObject('test.txt')
    const fileInput = wrapper.find('input[type="file"]')

    // Mock the files property
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      writable: false
    })

    await fileInput.trigger('change')

    expect(wrapper.emitted('files-selected')).toBeTruthy()
    expect(wrapper.emitted('files-selected')?.[0]).toEqual([[file]])
  })

  it('handles drag and drop', async () => {
    const wrapper = mount(FileUploadArea, {
      props: { files: [] }
    })

    const file = createMockFileObject('dropped.txt')
    const dropEvent = createFileDropEvent([file])

    const dropZone = wrapper.find('.border-dashed')
    await dropZone.trigger('dragover')
    
    // Manually call the drop handler since jsdom doesn't fully support drag events
    const component = wrapper.vm as any
    component.handleDrop(dropEvent)

    expect(wrapper.emitted('files-selected')).toBeTruthy()
  })

  it('validates file size', async () => {
    const wrapper = mount(FileUploadArea, {
      props: { 
        files: [],
        maxFileSize: 1024 // 1KB
      }
    })

    const largeFile = createMockFileObject('large.txt', 2048) // 2KB
    const fileInput = wrapper.find('input[type="file"]')

    Object.defineProperty(fileInput.element, 'files', {
      value: [largeFile],
      writable: false
    })

    await fileInput.trigger('change')

    expect(wrapper.emitted('upload-error')).toBeTruthy()
    expect(wrapper.emitted('upload-error')?.[0][0]).toContain('too large')
  })

  it('validates file count', async () => {
    const existingFiles = [
      createMockFile({ id: '1' }),
      createMockFile({ id: '2' })
    ]

    const wrapper = mount(FileUploadArea, {
      props: { 
        files: existingFiles,
        maxFiles: 2
      }
    })

    const newFile = createMockFileObject('new.txt')
    const fileInput = wrapper.find('input[type="file"]')

    Object.defineProperty(fileInput.element, 'files', {
      value: [newFile],
      writable: false
    })

    await fileInput.trigger('change')

    expect(wrapper.emitted('upload-error')).toBeTruthy()
    expect(wrapper.emitted('upload-error')?.[0][0]).toContain('Maximum 2 files')
  })

  it('shows drag over state', async () => {
    const wrapper = mount(FileUploadArea, {
      props: { files: [] }
    })

    const dropZone = wrapper.find('.border-dashed')
    await dropZone.trigger('dragover')

    expect(wrapper.find('.border-blue-400').exists()).toBe(true)
    expect(wrapper.find('.bg-blue-50').exists()).toBe(true)
  })

  it('resets drag over state on drag leave', async () => {
    const wrapper = mount(FileUploadArea, {
      props: { files: [] }
    })

    const dropZone = wrapper.find('.border-dashed')
    await dropZone.trigger('dragover')
    await dropZone.trigger('dragleave')

    expect(wrapper.find('.border-blue-400').exists()).toBe(false)
  })

  it('formats file sizes correctly', () => {
    const files = [
      createMockFile({ size: 1024 }), // 1 KB
      createMockFile({ size: 1048576 }), // 1 MB
      createMockFile({ size: 1073741824 }) // 1 GB
    ]

    const wrapper = mount(FileUploadArea, {
      props: { files }
    })

    expect(wrapper.text()).toContain('1 KB')
    expect(wrapper.text()).toContain('1 MB')
    expect(wrapper.text()).toContain('1 GB')
  })

  it('shows overall upload progress', () => {
    const wrapper = mount(FileUploadArea, {
      props: {
        files: [],
        isUploading: true,
        uploadProgress: 75
      }
    })

    expect(wrapper.text()).toContain('Overall Progress')
    expect(wrapper.text()).toContain('75%')
  })

  it('disables remove button during upload', () => {
    const files = [
      createMockFile({
        status: 'uploading'
      })
    ]

    const wrapper = mount(FileUploadArea, {
      props: { files }
    })

    const removeButton = wrapper.find('.remove-button')
    expect(removeButton.attributes('disabled')).toBeDefined()
  })
})