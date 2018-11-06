from autograd import grad
import numpy as np

from angler.gradients import *

class Objective():

    """ Stores the objective function and its arguments 
        Useful for automatically selecting adjoint problems
    """
    def __init__(self, J, arg_list):        

        self.arg_list = arg_list
        self.J = J

        sig = signature(J)
        num_args_J = len(sig.parameters.items())
        assert len(arg_list) == num_args_J

    def is_linear(self):
        # is the objective function purely a function of linear fields?
        for arg in self.arg_list:
            if arg.nl:
                return False
        return True

    @property
    def J(self):
        # objective function
        return self._J

    @J.setter
    def J(self, J_new):
        # when objective function is reset, re-solve for the partials
        self._J = J_new
        self._autograd_J()
        self._get_gradients()

    def _autograd_J(self):

        sig = signature(self._J)
        num_args = len(sig.parameters.items())

        # note: eventually want to check whether J has eps_nl argument, then switch between linear and nonlinear depending.
        dJ_list = []

        for arg_index in range(num_args):
            dJ_list.append(grad(self._J, arg_index))
        self.dJ_list = dJ_list

    def _get_gradients(self):
        # loads in the gradient functions from the arg_list
        grad_fn_list = []
        for arg in self.arg_list:
            grad_fn_list.append(arg.gradient)
        self.grad_fn_list = grad_fn_list


class obj_arg():
    """ Defines an argument to the objective function.
        Specifies name, field component, and whether field is nonlinear
        Selects the corresponding gradient for the problem
    """

    def __init__(self, name, component='Ez', nl=False):

        # give a name to this argument (ex: "Ez_lin")
        self.name = str(name)

        # get field component
        assert component in ['Ex','Ey','Ez','Hx','Hy','Hz']
        self.component = component

        # whether this is nonlinear field
        self.nl = nl

        self._select_gradient()

    def _select_gradient(self):

        # selects the correct gradient function.  
        self.gradient = None    # default

        if self.component == 'Ez':
            if not self.nl:
                self.gradient = grad_linear_Ez
            else:
                self.gradient = grad_kerr_Ez

        if self.component == 'Hz':
            if not self.nl:
                self.gradient = grad_linear_Ez
            else:
                self.gradient = grad_kerr_Ez

        if self.gradient is None:
            raise ValueError("Couldn't find gradient for argument: '{}'".format(self.name))

if __name__ == "__main__":

    # example

    # define the arguments to the objective function
    f1 = obj_arg('Ez_lin', component='Ez', nl=False)
    f2 = obj_arg('Hx_lin', component='Hz', nl=False)
    f3 = obj_arg('Ex_nl', component='Ex', nl=True)
    arg_list = [f1, f2, f3]

    # define the objective function
    import autograd.numpy as npa
    def J(f1, f2, f3):

        A = npa.sum(npa.abs(f1*f2))
        B = npa.sum(npa.abs(f2*f3))
        C = npa.abs(A - B)
        return -C

    objective = Objective(J, arg_list)

    Nx = 40
    Ny = 4
    F1 = np.random.random((Nx, Ny))
    F2 = np.ones((Nx, Ny))
    F3 = np.random.random((Nx, Ny))
