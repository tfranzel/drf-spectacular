const swagger_settings  = {{settings|safe}}

const ui = SwaggerUIBundle({
  url: "{{schema_url|safe}}",
  dom_id: '#swagger-ui',
  presets: [
    SwaggerUIBundle.presets.apis,
  ],
  plugin: [
    SwaggerUIBundle.plugins.DownloadUrl
  ],
  layout: "BaseLayout",
  requestInterceptor: (request) => {
    request.headers['X-CSRFToken'] = "{{csrf_token}}"
    return request;
  },
  onComplete: () => {
    var authWrapper = document.getElementsByClassName('auth-wrapper')[0]
    var djangoLoginButton = document.createDocumentFragment();
    Array.from(document.getElementById("django-login-button-on-ui-complete").children).forEach(e => {
      djangoLoginButton.appendChild(e)
    })
    authWrapper.prepend(djangoLoginButton)
    authWrapper.style.alignItems = 'center'
  },
  ...swagger_settings
})
