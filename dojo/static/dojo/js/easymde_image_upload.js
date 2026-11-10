/*
 * Image upload for the EasyMDE markdown editors on the Add / Edit Finding pages.
 *
 * Pasting (Ctrl+V) or dropping an image into an editor uploads it to
 * test/<id>/upload_finding_image and inserts ![](url) at the cursor.
 *
 * Usage: new EasyMDE(Object.assign({...base options...}, ddImageUploadOptions(uploadUrl)))
 */
(function (window) {
    "use strict";

    // Keep in sync with FINDING_IMAGE_MAX_SIZE in dojo/test/ui/views.py
    var MAX_IMAGE_SIZE = 5 * 1024 * 1024;

    function csrfToken() {
        var input = document.querySelector("input[name=csrfmiddlewaretoken]");
        return input ? input.value : "";
    }

    function uploadImage(uploadUrl, file, onSuccess, onError) {
        var data = new FormData();
        data.append("image", file);

        fetch(uploadUrl, {
            method: "POST",
            body: data,
            credentials: "same-origin",
            headers: {"X-CSRFToken": csrfToken()},
        })
            .then(function (response) {
                return response.json()
                    .catch(function () { return {}; })
                    .then(function (body) {
                        if (response.ok && body.url) {
                            onSuccess(body.url);
                        } else {
                            onError(body.error || "Image upload failed (HTTP " + response.status + ").");
                        }
                    });
            })
            .catch(function () {
                onError("Image upload failed: the server could not be reached.");
            });
    }

    window.ddImageUploadOptions = function (uploadUrl) {
        if (!uploadUrl) {
            return {};
        }
        return {
            uploadImage: true,
            imageAccept: "image/png, image/jpeg, image/gif, image/webp",
            imageMaxSize: MAX_IMAGE_SIZE,
            imageUploadFunction: function (file, onSuccess, onError) {
                uploadImage(uploadUrl, file, onSuccess, onError);
            },
        };
    };
})(window);
