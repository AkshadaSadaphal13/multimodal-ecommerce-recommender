import { useRef, useState } from "react";

function SearchBar({
  value,
  onChange,
  onSearch,
  loading,
  onImageSelect,
}) {
  const fileInputRef = useRef(null);

  const [selectedImage, setSelectedImage] =
    useState(null);

  const [imagePreview, setImagePreview] =
    useState(null);

  const [isDragging, setIsDragging] =
    useState(false);

  const [imageError, setImageError] =
    useState("");


  /* =========================================================
     IMAGE VALIDATION
  ========================================================= */

  const validateImage = (file) => {

    if (!file) {
      return false;
    }

    const allowedTypes = [
      "image/jpeg",
      "image/jpg",
      "image/png",
      "image/webp",
    ];

    if (!allowedTypes.includes(file.type)) {

      setImageError(
        "Please upload JPG, PNG or WEBP image."
      );

      return false;
    }


    const maxSize =
      10 * 1024 * 1024;

    if (file.size > maxSize) {

      setImageError(
        "Image size must be less than 10 MB."
      );

      return false;
    }


    setImageError("");

    return true;
  };


  /* =========================================================
     PROCESS IMAGE
  ========================================================= */

  const processImage = (file) => {

    if (!validateImage(file)) {
      return;
    }


    setSelectedImage(file);


    const previewUrl =
      URL.createObjectURL(file);

    setImagePreview(
      previewUrl
    );


    /*
      Send image information to parent.

      This will be used later by App.jsx
      for the actual ResNet50 image-search API.
    */

    if (onImageSelect) {

      onImageSelect(
        file,
        previewUrl
      );

    }

  };


  /* =========================================================
     FILE INPUT
  ========================================================= */

  const handleFileChange = (
    event
  ) => {

    const file =
      event.target.files?.[0];

    if (file) {
      processImage(file);
    }

    /*
      Reset input so the user can
      select the same image again.
    */

    event.target.value = "";
  };


  /* =========================================================
     OPEN FILE SELECTOR
  ========================================================= */

  const openFilePicker = () => {

    if (loading) {
      return;
    }

    fileInputRef.current?.click();

  };


  /* =========================================================
     DRAG EVENTS
  ========================================================= */

  const handleDragOver = (
    event
  ) => {

    event.preventDefault();

    if (!loading) {
      setIsDragging(true);
    }

  };


  const handleDragLeave = (
    event
  ) => {

    event.preventDefault();

    setIsDragging(false);

  };


  const handleDrop = (
    event
  ) => {

    event.preventDefault();

    setIsDragging(false);


    if (loading) {
      return;
    }


    const file =
      event.dataTransfer.files?.[0];


    if (file) {
      processImage(file);
    }

  };


  /* =========================================================
     REMOVE IMAGE
  ========================================================= */

  const removeImage = () => {

    if (imagePreview) {

      URL.revokeObjectURL(
        imagePreview
      );

    }


    setSelectedImage(null);

    setImagePreview(null);

    setImageError("");


    if (onImageSelect) {

      onImageSelect(
        null,
        null
      );

    }

  };


  /* =========================================================
     TEXT CLEAR
  ========================================================= */

  const clearSearch = () => {

    onChange("");

  };


  /* =========================================================
     SEARCH SUBMIT
  ========================================================= */

  const handleSubmit = (
    event
  ) => {

    event.preventDefault();


    if (loading) {
      return;
    }


    const hasText =
      value &&
      value.trim().length > 0;


    const hasImage =
      selectedImage !== null;


    /*
      Allow:

      1. Text only
      2. Image only
      3. Text + Image

      But don't allow an empty search.
    */

    if (
      !hasText &&
      !hasImage
    ) {

      return;

    }


    /*
      Pass both values to parent.

      Current App.jsx can still work because
      its onSearch function doesn't require
      these arguments.

      We will update App.jsx in the next step
      to actually send the image to FastAPI.
    */

    onSearch(
      value?.trim() || "",
      selectedImage
    );

  };


  /* =========================================================
     IMAGE SEARCH LABEL
  ========================================================= */

  const getSearchMode = () => {

    const hasText =
      value &&
      value.trim().length > 0;

    const hasImage =
      selectedImage !== null;


    if (
      hasText &&
      hasImage
    ) {

      return "Text + Visual Search";

    }


    if (hasImage) {

      return "Visual Search";

    }


    return "AI Semantic Search";

  };


  return (

    <div className="multimodal-search-container">


      {/* =====================================================
          MAIN SEARCH FORM
      ===================================================== */}

      <form
        className="search-form"
        onSubmit={
          handleSubmit
        }
      >


        {/* ===================================================
            TEXT SEARCH
        =================================================== */}

        <div className="search-input-wrapper">

          <span className="search-icon">
            ⌕
          </span>


          <input
            type="text"
            value={value}
            onChange={(event) =>
              onChange(
                event.target.value
              )
            }
            placeholder="Search products, brands and more..."
            disabled={loading}
          />


          {value &&
            !loading && (

            <button
              type="button"
              className="clear-button"
              onClick={
                clearSearch
              }
              aria-label="Clear search"
            >
              ×
            </button>

          )}

        </div>


        {/* ===================================================
            IMAGE BUTTON
        =================================================== */}

        <button
          type="button"
          className={
            selectedImage
              ? "image-upload-button active"
              : "image-upload-button"
          }
          onClick={
            openFilePicker
          }
          disabled={loading}
          title="Search using an image"
          aria-label="Upload product image"
        >

          <span className="upload-icon">
            📷
          </span>

          <span className="upload-text">
            Image
          </span>

        </button>


        {/* ===================================================
            HIDDEN FILE INPUT
        =================================================== */}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/webp"
          onChange={
            handleFileChange
          }
          style={{
            display: "none",
          }}
        />


        {/* ===================================================
            SEARCH BUTTON
        =================================================== */}

        <button
          type="submit"
          className="search-button"
          disabled={
            loading ||
            (
              !value?.trim() &&
              !selectedImage
            )
          }
        >

          {loading ? (

            <>

              <span className="button-spinner"></span>

              Searching...

            </>

          ) : (

            <>

              Search

              <span className="search-arrow">
                →
              </span>

            </>

          )}

        </button>

      </form>


      {/* =====================================================
          IMAGE DROP ZONE
      ===================================================== */}

      {!selectedImage && !loading && (

        <div
          className={
            isDragging
              ? "image-drop-zone dragging"
              : "image-drop-zone"
          }
          onDragOver={
            handleDragOver
          }
          onDragLeave={
            handleDragLeave
          }
          onDrop={
            handleDrop
          }
        >

          <div className="drop-zone-icon">
            📷
          </div>


          <div className="drop-zone-content">

            <strong>
              Search with an image
            </strong>

            <span>
              Drag & drop a product image
              here or
            </span>

            <button
              type="button"
              onClick={
                openFilePicker
              }
            >
              Browse files
            </button>

          </div>


          <small>
            JPG, PNG or WEBP • Max 10 MB
          </small>

        </div>

      )}


      {/* =====================================================
          IMAGE PREVIEW
      ===================================================== */}

      {selectedImage &&
        imagePreview && (

        <div className="selected-image-container">


          <div className="selected-image-preview">

            <img
              src={imagePreview}
              alt="Selected product"
            />

          </div>


          <div className="selected-image-info">

            <span className="selected-image-label">
              ✓ IMAGE READY
            </span>


            <strong>
              {selectedImage.name}
            </strong>


            <small>
              {(
                selectedImage.size /
                (1024 * 1024)
              ).toFixed(2)}{" "}
              MB
            </small>


            <span className="search-mode">

              {getSearchMode()}

            </span>

          </div>


          <button
            type="button"
            className="remove-image-button"
            onClick={
              removeImage
            }
            disabled={loading}
            aria-label="Remove image"
          >
            ×
          </button>

        </div>

      )}


      {/* =====================================================
          IMAGE ERROR
      ===================================================== */}

      {imageError && (

        <div className="image-upload-error">

          <span>
            !
          </span>

          {imageError}

        </div>

      )}


      {/* =====================================================
          SEARCH MODE INDICATOR
      ===================================================== */}

      {(value?.trim() ||
        selectedImage) && (

        <div className="search-mode-indicator">

          <span className="mode-label">
            Search mode:
          </span>


          <span className="mode-pill">

            <span className="mode-dot"></span>

            {getSearchMode()}

          </span>


          {selectedImage && (

            <span className="mode-signal">

              🖼 Visual signal enabled

            </span>

          )}

        </div>

      )}

    </div>

  );

}

export default SearchBar;