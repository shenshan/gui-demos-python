import datajoint as dj
import dash
import dash_table
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from costagui_demos.dj_tables import lab, subject, hardware
from costagui_demos import dj_utils, component_utils, callback_utils
import datetime

DataJointTable = dj.user_tables.OrderedClass


class TableBlock:
    def __init__(self, table: DataJointTable, app=None, include_parts=False,
                 table_height='800px',
                 table_width='800px',
                 button_style={
                    'marginRight': '1em',
                    'marginBottom': '1em'},
                 messagebox_style={
                    'width': 750,
                    'height': 50,
                    'marginBottom': '1em',
                    'display': 'block'},
                 ):
        self.app = app
        self.table = table
        self.table_name = table.__name__.lower()
        self.primary_key = table.heading.primary_key
        self.attrs = table.heading.attributes
        self.field_names = table.heading.names

        self.display_table = component_utils.create_display_table(
            self.table, f'{self.table_name}-table',
            height=table_height, width=table_width)

        self.add_button = html.Button(
            children=f'Add a {self.table_name} record',
            id=f'add-{self.table_name}-button', n_clicks=0,
            style=button_style)

        self.delete_button = html.Button(
            children=f'Delete the current record',
            id=f'delete-{self.table_name}-button', n_clicks=0,
            style=button_style
        )

        self.update_button = html.Button(
            children='Update the current record',
            id=f'update-{self.table_name}-button', n_clicks=0,
            style=button_style
        )

        self.add_modal = component_utils.create_modal(
            self.table, self.table_name, include_parts=include_parts,
            mode='add'
        )

        self.update_modal = component_utils.create_modal(
            self.table, self.table_name, include_parts=include_parts,
            mode='update'
        )

        self.delete_message_box = dcc.Textarea(
            id=f'delete-{self.table_name}-message-box',
            value=f'Delete {self.table_name} message:',
            style=messagebox_style
        )

        self.delete_confirm = dcc.ConfirmDialog(
            id=f'delete-{self.table_name}-confirm',
            message='Are you sure to delete the record?',
        ),

        if self.app is not None and hasattr(self, 'callbacks'):
            self.callbacks(self.app)

    def create_default_layout(self):
        self.layout = html.Div(
            html.Div(
                className="row app-body",
                children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                self.add_button,
                                                style={'display': 'inline-block'}),
                                            html.Div(
                                                self.delete_button,
                                                style={'display': 'inline-block'}),
                                            html.Div(
                                                self.update_button,
                                                style={'display': 'inline-block'})
                                        ],
                                    ),
                                    self.delete_message_box,
                                ]
                            ),

                            html.Div(
                                [
                                    html.H6(f'{self.table.__name__}'),
                                    self.display_table
                                ],
                                style={'marginRight': '1em',
                                       'display': 'inline-block'}),
                        ]
                    ),
                    # confirmation dialogue
                    html.Div(self.delete_confirm),
                    # modals
                    self.update_modal,
                    self.add_modal
                ]
            )
        )

    def callbacks(self, app):

        @app.callback(
            [
                Output(f'delete-{self.table_name}-button', 'disabled'),
                Output(f'update-{self.table_name}-button', 'disabled')
            ],
            [
                Input(f'{self.table_name}-table', 'selected_rows')
            ])
        def set_button_enabled_state(selected_rows):
            if selected_rows:
                disabled = False
            else:
                disabled = True
            return disabled, disabled

        @app.callback(
            Output(f'delete-{self.table_name}-confirm', 'displayed'),
            [Input(f'delete-{self.table_name}-button', 'n_clicks')])
        def display_delete_confirm(n_clicks):
            if n_clicks:
                return True
            return False

        @app.callback(
            [
                Output(f'{self.table_name}-table', 'data'),
                Output(f'delete-{self.table_name}-message-box', 'value')
            ],
            [
                Input(f'add-{self.table_name}-close', 'n_clicks'),
                Input(f'delete-{self.table_name}-confirm', 'submit_n_clicks'),
                Input(f'update-{self.table_name}-close', 'n_clicks'),
                Input(f'{self.table_name}-table', 'selected_rows')
            ],
            [
                State(f'{self.table_name}-table', 'data'),
            ]
        )
        def update_table_data(
                n_clicks_add_close, n_clicks_delete, n_clicks_update_close,
                selected_rows, data):

            delete_message = 'Delete subject message:\n'
            ctx = dash.callback_context
            triggered_component = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_component == f'delete-{self.table_name}-confirm' and selected_rows:
                current_record = callback_utils.clean_single_gui_record(
                    data[selected_rows[0]], self.attrs)
                pk = {k: v for k, v in current_record.items()
                      if k in self.primary_key}
                try:
                    (self.table & pk).delete()
                    delete_message = delete_message + \
                        f'Successfully deleted record {pk}!'
                except Exception as e:
                    delete_message = delete_message + \
                        f'Error in deleting record {pk}: {str(e)}.'
                data = self.table.fetch(as_dict=True)
            elif triggered_component in (f'add-{self.table_name}-close',
                                         f'update-{self.table_name}-close'):
                data = self.table.fetch(as_dict=True)

            return data, delete_message

        def toggle_modal(
                n_open, n_close,
                is_open, data, selected_rows,
                modal_data, mode):

            ctx = dash.callback_context
            triggered_component = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_component == f'{mode}-{self.table_name}-button':
                if selected_rows:
                    modal_data = [data[selected_rows[0]]]
                else:
                    if mode == 'add':
                        modal_data = [{k: '' for k in self.field_names}]
                    elif mode == 'update':
                        raise ValueError('Update Modal open without a particular row selected')

                modal_open = not is_open if n_open or n_close else is_open

            elif triggered_component == f'{mode}-{self.table_name}-close':
                modal_open = not is_open if n_open or n_close else is_open

            else:
                modal_open = is_open

            return modal_open, modal_data

        @app.callback(
            [
                Output(f'add-{self.table_name}-modal', 'is_open'),
                Output(f'add-{self.table_name}-table', 'data'),
            ],
            [
                Input(f'add-{self.table_name}-button', 'n_clicks'),
                Input(f'add-{self.table_name}-close', 'n_clicks'),
            ],
            [
                State(f'add-{self.table_name}-modal', 'is_open'),
                State(f'{self.table_name}-table', 'data'),
                State(f'{self.table_name}-table', 'selected_rows'),
                State(f'add-{self.table_name}-table', 'data'),
            ],
        )
        def toggle_add_modal(*args):
            return toggle_modal(*args, mode='add')

        @app.callback(
            [
                Output(f'update-{self.table_name}-modal', 'is_open'),
                Output(f'update-{self.table_name}-table', 'data'),
            ],
            [
                Input(f'update-{self.table_name}-button', 'n_clicks'),
                Input(f'update-{self.table_name}-close', 'n_clicks'),
            ],
            [
                State(f'update-{self.table_name}-modal', 'is_open'),
                State(f'{self.table_name}-table', 'data'),
                State(f'{self.table_name}-table', 'selected_rows'),
                State(f'update-{self.table_name}-table', 'data'),
            ],
        )
        def toggle_update_modal(*args):
            return toggle_modal(*args, mode='update')

        @app.callback(
            Output(f'add-{self.table_name}-message', 'value'),
            [
                Input(f'add-{self.table_name}-confirm', 'n_clicks'),
                Input(f'add-{self.table_name}-close', 'n_clicks')
            ],
            [
                State(f'add-{self.table_name}-table', 'data'),
                State(f'add-{self.table_name}-message', 'value')
            ]
        )
        def add_record(
                n_clicks_add, n_clicks_close,
                new_data, add_message):

            ctx = dash.callback_context
            triggered_component = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_component == f'add-{self.table_name}-confirm':

                entry = {k: v for k, v in new_data[0].items() if v != ''}

                add_message = 'Add message:'
                try:
                    pk = {k: v
                          for k, v in callback_utils.clean_single_gui_record(
                            entry, self.attrs).items()
                          if k in self.primary_key}
                    if (self.table & pk):
                        add_message = add_message + \
                            f'\nWarning: record {pk} exists in database'
                    else:
                        self.table.insert1(entry)
                        add_message = add_message + \
                            f'\nSuccessful insertion to {self.table_name}.'

                except Exception as e:
                    add_message = add_message + \
                        f'\nError inserting into {self.table_name}: {str(e)}'

            elif triggered_component == f'add-{self.table_name}-close':
                add_message = 'Add message:'

            return add_message

        @app.callback(
            Output(f'update-{self.table_name}-message', 'value'),
            [
                Input(f'update-{self.table_name}-confirm', 'n_clicks')
            ],
            [
                State(f'update-{self.table_name}-table', 'data'),
            ],
        )
        def update_record(
                n_clicks, update_data):

            new = update_data[0]
            pk = {k: v for k, v in new.items() if k in self.primary_key}
            return callback_utils.update_table(self.table, new, pk)
