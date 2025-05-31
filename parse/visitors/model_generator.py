"""Famix model generator for PowerBuilder.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Visitor/PWBFamixModelGenerator.class.st
"""

from dataclasses import dataclass, field

from model.pb_famix import (
    FamixBuilder,
    FamixClass,
    FamixTrait,
)


@dataclass
class ModelGeneratorState:
    """State for Famix model generator."""
    builder: FamixBuilder | None = None
    classes: dict[str, FamixClass] = field(default_factory=dict)
    traits: dict[str, FamixTrait] = field(default_factory=dict)


class PowerBuilderFamixModelGenerator:
    """Generator for creating Famix metamodel for PowerBuilder.

    Features:
    - Defines PowerBuilder-specific classes and traits
    - Defines class hierarchy and inheritance
    - Defines properties and relations
    - Generates complete metamodel
    """

    PACKAGE_NAME = 'Famix-PowerBuilder-Entities'
    PREFIX = 'FamixPWB'

    def __init__(self) -> None:
        """Initialize generator."""
        self.state = ModelGeneratorState()
        self.state.builder = self.new_builder()

    def new_builder(self) -> FamixBuilder:
        """Create new Famix builder.

        Returns:
            Configured Famix builder
        """
        builder = FamixBuilder()
        builder.with_importing_context = True
        return builder

    def define_classes(self) -> None:
        """Define PowerBuilder-specific classes.

        Creates classes for:
        - Library and components
        - Behavioral elements
        - Variables and attributes
        - Major objects (files)
        - Types
        - Associations
        """
        # Library and components
        self.state.classes['Library'] = self.state.builder.new_class('Library')
        self.state.classes['GraphicComponent'] = self.state.builder.new_class('GraphicComponent')

        # Behavioral elements
        self.state.classes['Behavioral'] = self.state.builder.new_class('Behavioral')
        self.state.classes['Event'] = self.state.builder.new_class('Event')
        self.state.classes['Routine'] = self.state.builder.new_class('Routine')
        self.state.classes['SqlQuery'] = self.state.builder.new_class('SqlQuery')
        self.state.classes['SubRoutine'] = self.state.builder.new_class('SubRoutine')

        # Variables and attributes
        self.state.classes['Variable'] = self.state.builder.new_class('Variable')
        self.state.classes['Attribute'] = self.state.builder.new_class('Attribute')
        self.state.classes['Parameter'] = self.state.builder.new_class('Parameter')
        self.state.classes['SharedVariable'] = self.state.builder.new_class('SharedVariable')
        self.state.classes['LocalVariable'] = self.state.builder.new_class('LocalVariable')
        self.state.classes['GlobalVariable'] = self.state.builder.new_class('GlobalVariable')
        self.state.classes['InstanceVariable'] = self.state.builder.new_class('InstanceVariable')

        # Methods and functions
        self.state.classes['Function'] = self.state.builder.new_class('Function')
        self.state.classes['Trigger'] = self.state.builder.new_class('Trigger')
        self.state.classes['Argument'] = self.state.builder.new_class('Argument')
        self.state.classes['FunctionReturn'] = self.state.builder.new_class('FunctionReturn')

        # Major objects
        self.state.classes['MajorObject'] = self.state.builder.new_class('MajorObject')
        self.state.classes['DataWindow'] = self.state.builder.new_class('DataWindow')
        self.state.classes['UserObject'] = self.state.builder.new_class('UserObject')
        self.state.classes['Window'] = self.state.builder.new_class('Window')
        self.state.classes['Structure'] = self.state.builder.new_class('Structure')
        self.state.classes['GlobalFunction'] = self.state.builder.new_class('GlobalFunction')
        self.state.classes['MenuObject'] = self.state.builder.new_class('MenuObject')
        self.state.classes['Application'] = self.state.builder.new_class('Application')
        self.state.classes['Query'] = self.state.builder.new_class('Query')
        self.state.classes['BehaviorSignature'] = self.state.builder.new_class('BehaviorSignature')

        # Types
        self.state.traits['AbstractType'] = self.state.builder.new_trait('AbstractType')
        self.state.classes['CustomType'] = self.state.builder.new_class('CustomType')
        self.state.classes['BasicType'] = self.state.builder.new_class('BasicType')

        # Associations
        self.state.classes['Access'] = self.state.builder.new_class('Access')
        self.state.classes['Invocation'] = self.state.builder.new_class('Invocation')
        self.state.classes['VariableAccess'] = self.state.builder.new_class('VariableAccess')
        self.state.classes['Reference'] = self.state.builder.new_class('Reference')

    def define_traits(self) -> None:
        """Define PowerBuilder-specific traits."""
        self.state.traits['PBTNamed'] = self.state.builder.new_trait('PBTNamed')
        self.state.traits['PBTWithMethods'] = self.state.builder.new_trait('PBTWithMethods')

    def define_hierarchy(self) -> None:
        """Define class hierarchy and inheritance.

        Sets up:
        - Trait inheritance
        - Class inheritance
        - Trait usage
        """
        # Trait inheritance
        self.state.traits['PBTNamed'].inherits_from('TNamedEntity')
        self.state.traits['PBTWithMethods'].inherits_from('TWithMethods')

        # Library and components
        self.state.classes['Library'].inherits_from(['TNamedEntity', 'TSourceEntity'])
        self.state.classes['GraphicComponent'].inherits_from(['TSourceEntity', 'TWithAttributes', 'Behavioral'])

        # Behavioral elements
        self.state.classes['Event'].inherits_from(['Behavioral', 'TMethod', 'TInvocable'])
        self.state.classes['Event'].uses_trait('PBTNamed', exclude=['mooseNameOn'])

        self.state.classes['Routine'].inherits_from(['Behavioral', 'TFunction'])
        self.state.classes['Routine'].uses_trait('PBTNamed', exclude=['mooseNameOn'])

        self.state.classes['Trigger'].inherits_from(['TWithAttributes', 'Behavioral', 'TMethod'])
        self.state.classes['Trigger'].uses_trait('PBTNamed', exclude=['mooseNameOn'])

        self.state.classes['SubRoutine'].inherits_from(['Behavioral', 'TMethod', 'TInvocable'])
        self.state.classes['SubRoutine'].uses_trait('PBTNamed', exclude=['mooseNameOn'])

        # Variables and attributes
        self.state.classes['Variable'].inherits_from(['TSourceEntity', 'TNamedEntity', 'TWithTypes', 'TAccessible'])
        self.state.classes['Parameter'].inherits_from(['TSourceEntity', 'TNamedEntity', 'TWithTypes', 'TAccessible'])
        self.state.classes['SharedVariable'].inherits_from(['Attribute'])
        self.state.classes['GlobalVariable'].inherits_from(['Attribute'])
        self.state.classes['LocalVariable'].inherits_from(['Variable'])
        self.state.classes['InstanceVariable'].inherits_from(['Attribute'])

        # Major objects
        self.state.classes['MajorObject'].inherits_from([
            'TSourceEntity',
            'TNamedEntity',
            'TWithAttributes',
            'TWithAccesses',
            'TWithFunctions',
            'TWithReferences',
        ])
        self.state.classes['MajorObject'].uses_trait('PBTWithMethods', exclude=['numberOfLinesOfCode'])

        self.state.classes['UserObject'].inherits_from(['MajorObject', 'AbstractType', 'TWithInvocations'])
        self.state.classes['Window'].inherits_from(['MajorObject', 'TWithInvocations'])
        self.state.classes['DataWindow'].inherits_from(['MajorObject', 'TWithInvocations'])
        self.state.classes['Structure'].inherits_from(['MajorObject'])
        self.state.classes['GlobalFunction'].inherits_from(['MajorObject', 'TWithInvocations', 'AbstractType'])
        self.state.classes['MenuObject'].inherits_from(['MajorObject'])
        self.state.classes['Application'].inherits_from(['MajorObject'])
        self.state.classes['Query'].inherits_from(['MajorObject'])

        # Types
        self.state.traits['AbstractType'].uses_trait('PBTNamed', exclude=['mooseNameOn'])
        self.state.traits['AbstractType'].inherits_from(['TType', 'TReferenceable'])
        self.state.classes['CustomType'].inherits_from(['AbstractType'])
        self.state.classes['BasicType'].inherits_from(['AbstractType'])

        # Associations
        self.state.classes['Access'].inherits_from(['TSourceEntity', 'TAccess'])
        self.state.classes['VariableAccess'].inherits_from(['TSourceEntity', 'TAccess'])
        self.state.classes['Reference'].inherits_from(['TSourceEntity', 'TReference'])
        self.state.classes['Invocation'].inherits_from(['TInvocation', 'THasSignature', 'TSourceEntity'])

    def define_properties(self) -> None:
        """Define class properties.

        Sets up properties for:
        - Metrics (cyclomatic complexity)
        - Arguments and parameters
        - Methods and functions
        - Attributes
        """
        # Metrics
        self.state.classes['MajorObject'].add_property('cyclomaticComplexity', 'Number')
        self.state.classes['Behavioral'].add_property('cyclomaticComplexity', 'Number')

        # Arguments and parameters
        self.state.classes['Argument'].add_property('argumentValue', 'Object')
        self.state.classes['Parameter'].add_property('parameterOption', 'Object')
        self.state.classes['Parameter'].add_property('parameterType', 'String')
        self.state.classes['Parameter'].add_property('startPos', 'Number')

        # Methods and functions
        self.state.classes['Function'].add_property('returnType', 'Object')
        self.state.classes['FunctionReturn'].add_property('type', 'Object')
        self.state.classes['FunctionReturn'].add_property('returnValue', 'Object')
        self.state.classes['FunctionReturn'].add_property('doesBelongToSingleLineIfStatement', 'Boolean')

        # Attributes
        self.state.classes['Attribute'].add_property('attributeType', 'Object')
        self.state.classes['Behavioral'].add_property('accessModifier', 'String')

    def define_relations(self) -> None:
        """Define class relations.

        Sets up relations for:
        - Variables and behavioral elements
        - DataWindow components
        - Libraries and objects
        - Invocations and arguments
        - Behavioral elements and returns
        - Parameters
        """
        # Variables and behavioral
        self.state.builder.add_many_to_one(
            source=self.state.classes['Variable'],
            source_property='behavioral',
            target=self.state.classes['Behavioral'],
            target_property='variables',
        )

        # DataWindow components
        self.state.builder.add_one_to_many(
            source=self.state.classes['DataWindow'],
            source_property='graphicComponents',
            target=self.state.classes['GraphicComponent'],
            target_property='dataWindow',
        )

        # Libraries and objects
        self.state.builder.add_many_to_one(
            source=self.state.classes['MajorObject'],
            source_property='library',
            target=self.state.classes['Library'],
            target_property='userObjects',
        )

        # Invocations and arguments
        self.state.builder.add_one_to_many(
            source=self.state.classes['Invocation'],
            source_property='arguments',
            target=self.state.classes['Argument'],
            target_property='invocation',
        )

        # Behavioral and returns
        self.state.builder.add_one_to_many(
            source=self.state.classes['Behavioral'],
            source_property='returns',
            target=self.state.classes['FunctionReturn'],
            target_property='behavioral',
        )

        # Behavioral and signature
        self.state.builder.add_one_to_one(
            source=self.state.classes['Behavioral'],
            source_property='signature',
            target=self.state.classes['BehaviorSignature'],
            target_property='behavioral',
        )

        # Parameters
        self.state.builder.add_many_to_one(
            source=self.state.classes['Parameter'],
            source_property='behavioral',
            target=self.state.classes['Behavioral'],
            target_property='parameters',
        )

    def generate(self):
        """Generate complete Famix metamodel.

        Steps:
        1. Define traits
        2. Define classes
        3. Define hierarchy
        4. Define properties
        5. Define relations
        """
        self.define_traits()
        self.define_classes()
        self.define_hierarchy()
        self.define_properties()
        self.define_relations()
        return self.state.builder.build()
