/**
 * File Upload Middleware (Multer Configuration)
 * 
 * Handles multipart/form-data image uploads with validation.
 * Stores files in memory (no disk writes) for processing.
 */

import multer from 'multer';

// Configure multer to store files in memory
const storage = multer.memoryStorage();

// File filter to validate image types
function fileFilter(req, file, cb) {
  // Allowed MIME types
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];

  if (allowedTypes.includes(file.mimetype)) {
    // Accept file
    cb(null, true);
  } else {
    // Reject file
    cb(
      new Error(`Invalid file type: ${file.mimetype}. Allowed: PNG, JPEG, WebP`),
      false
    );
  }
}

// Configure multer
const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB max
    files: 1, // Only accept 1 file
  },
});

/**
 * Middleware to handle single image upload
 * Field name: "image"
 */
export const uploadImage = upload.single('image');

/**
 * Error handler for multer errors
 * Should be used after the upload middleware
 */
export function handleUploadErrors(err, req, res, next) {
  if (err instanceof multer.MulterError) {
    // Multer-specific errors
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        error: 'ValidationError',
        message: 'File size exceeds 10MB limit',
        code: 'FILE_TOO_LARGE',
      });
    }

    if (err.code === 'LIMIT_FILE_COUNT') {
      return res.status(400).json({
        error: 'ValidationError',
        message: 'Only one file allowed per request',
        code: 'TOO_MANY_FILES',
      });
    }

    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      return res.status(400).json({
        error: 'ValidationError',
        message: 'Unexpected file field. Use "image" as field name.',
        code: 'UNEXPECTED_FIELD',
      });
    }

    // Generic multer error
    return res.status(400).json({
      error: 'ValidationError',
      message: err.message,
      code: 'UPLOAD_ERROR',
    });
  }

  if (err) {
    // Custom validation errors (from fileFilter)
    return res.status(400).json({
      error: 'ValidationError',
      message: err.message,
      code: 'INVALID_FILE',
    });
  }

  // No error, continue
  next();
}

/**
 * Middleware to validate that file was uploaded
 * Should be used after uploadImage middleware
 */
export function validateImageUploaded(req, res, next) {
  if (!req.file) {
    return res.status(400).json({
      error: 'ValidationError',
      message: 'Missing required field: image',
      code: 'MISSING_IMAGE',
    });
  }

  // Validate file has buffer (should always be present with memoryStorage)
  if (!req.file.buffer) {
    return res.status(400).json({
      error: 'ValidationError',
      message: 'Image file is empty',
      code: 'EMPTY_IMAGE',
    });
  }

  next();
}

export default {
  uploadImage,
  handleUploadErrors,
  validateImageUploaded,
};

