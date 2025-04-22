from chope import *

# Bootstrap 5 CSS
bootstrap_css = link(
    href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/css/bootstrap.min.css",
    rel="stylesheet",
    integrity="sha384-SgOJa3DmI69IUzQ2PVdRZhwQ+dy64/BUtbMJw1MZ8t5HZApcHrRKUc4W0kG879m7",
    crossorigin="anonymous"
)

# Bootstrap 5 JS
bootstrap_js = script(
    src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js",
    integrity="sha384-k6d4wzSIapyDyv1kpU366/PK5hCdSbCRGRCMv+eplOQJWyd1fbcAu9OCUj5zNLiq",
    crossorigin="anonymous"
)

# Bootswatch Quartz Theme
bootswatch_css = link(
    rel="stylesheet",
    href="https://cdnjs.cloudflare.com/ajax/libs/bootswatch/5.3.3/quartz/bootstrap.min.css",
    integrity="sha512-K+FEHZnRHFnQ6iahLNQUCHNpKDHkrYxHZmzFjOJteRPjBhjLmOgJgGJsIYBDOS1wYxcSVvAcfg3ZFpm6tnbhOA==",
    crossorigin="anonymous",
    referrerpolicy="no-referrer"
)

# Alpine.js (deferred)
alpine_js = script(
    defer=True,
    src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"
)

# Google Material Symbols
material_icons = link(
    href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,200,1,1&icon_names=send",
    rel="stylesheet"
)

# HTMX
htmx_js = script(
    src="https://unpkg.com/htmx.org@2.0.4",
    integrity="sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+",
    crossorigin="anonymous"
)

# HTMX SSE
htmx_ext_sse_js = script(
    src="https://unpkg.com/htmx-ext-sse@2.2.2",
    integrity="sha384-Y4gc0CK6Kg+hmulDc6rZPJu0tqvk7EWlih0Oh+2OkAi1ZDlCbBDCQEE2uVk472Ky",
    crossorigin="anonymous"
)

navbar = nav(
    class_="navbar navbar-expand-lg bg-primary",
    data_bs_theme="dark",
)[
    div(class_="container-fluid")[
        a(class_="navbar-brand", href='',)["Jaiger"]
    ]
]

user_bubble = div(class_="card text-bg-light m-2")[
    p(class_="m-2")["Some quick example text to build on the card title and make up the bulk of the card's content."],
]

reply_bubble = div(class_="card m-2")[
    div(class_="card-body")[
        h6(class_="card-subtitle mb-2 text-muted",)["AI"],
        p(class_="card-text")["Some quick example text to build on the card title and make up the bulk of the card's content."],
    ]
]

reply_loading = div(class_="card m-2")[
    div(class_='card-footer')[
        div(class_='spinner-grow spinner-grow-sm text-light', role='status')[
            span(class_='visually-hidden')['Loading ...']
        ]
    ]
]

class UserBubble:
    def __new__(cls, content: str) -> Element:
        return div(class_='container d-flex justify-content-end', hx_swap_oob="beforebegin:#bubbles-end")[
            div(class_="card text-bg-light m-2")[
                p(class_="m-2")[
                    content
                ]
            ]
        ]

class ReplyBubble:
    def __new__(cls, content: str) -> Element:
        return div(class_='container d-flex justify-content-start', hx_swap_oob="beforebegin:#bubbles-end")[
            div(class_="card m-2")[
                div(class_="card-body")[
                    h6(class_="card-subtitle mb-2 text-muted")["AI"],
                    p(class_="card-text")[
                        content
                    ]
                ]
            ]
        ]

class ReplyLoading:
    def __new__(cls):
        return div(class_='container d-flex justify-content-start', hx_swap_oob="beforebegin:#bubbles-end", sse_swap="newResponse")[
            div(id="spinner", class_="card m-2")[
                div(class_="card-footer")[
                    div(class_="spinner-grow spinner-grow-sm text-light", role="status")[
                        span(class_="visually-hidden")["Loading ..."]
                    ]
                ]
            ]
        ]

class Root:
    def __new__(cls):
        return html[
            head[
                bootswatch_css,
                bootstrap_js,
                bootswatch_css,
                alpine_js,
                material_icons,
                htmx_js,
                htmx_ext_sse_js
            ],
            body(hx_ext="sse", sse_connect="/sse")[
                div(class_='d-flex flex-column vh-100')[
                    navbar,
                    div(id='bubbles-end'),
                    div(
                        class_='container d-flex flex-row flex-grow-1 align-items-end justify-content-center',
                        x_data="{ prompt: '', shift_down: false }"
                    )[
                        div('.d-flex.flex-column.flex-grow-1.m-2')[
                            textarea(
                                ':rows', 'prompt.split("\\n", 10).length',
                                '@keydown.enter', '''if (!shift_down) {$event.preventDefault(); $el.dispatchEvent(new Event("send")); prompt = ""}''',
                                '@keydown.shift', 'shift_down = true',
                                '@keyup.shift', 'shift_down = false',
                                name="prompt",
                                class_='form-control',
                                placeholder='Type your prompt here',
                                style='resize: none',
                                x_model='prompt',
                                hx_trigger="send",
                                hx_post="/prompt",
                                # hx_include="[name='prompt']",
                                hx_vals='js:{text: prompt}'
                            )
                        ],
                        div('.d-flex.flex-column.mb-2.mt-2')[
                            button(
                                '@click', 'prompt = ""',
                                ':disabled', "prompt === ''",
                                class_='btn btn-secondary',
                                hx_post="/prompt",
                                # hx_include="[name='prompt']",
                                hx_vals='js:{text: prompt}'
                            )[
                                span(class_="material-symbols-rounded")['send']
                            ]
                        ]
                    ]
                ]
            ]
        ]
