<template>

  <KModal
    :title="modalTitle"
    v-bind="modalTexts"
    :submitDisabled="blockControls"
    @submit="handleSubmit"
    @cancel="$emit('cancel')"
  >
    <!-- Classroom Selection Form -->
    <div v-if="atSelectClassroom" id="select-classroom">
      <KRadioButton
        v-for="classroom in availableClassrooms"
        :key="classroom.id"
        v-model="selectedClassroomId"
        :label="classroomLabel(classroom)"
        :value="classroom.id"
        :disabled="blockControls"
        data-test="radio-button"
      />
    </div>

    <!-- Learner Group Selection Form -->
    <div v-if="current.matches('SELECT_GROUPS')" id="select-learnergroup">
      <div v-if="current.matches('SELECT_GROUPS.LOADING')">
        <h1>Loading</h1>
      </div>
      <div v-else-if="current.matches('SELECT_GROUPS.FAILED')">
        <h1>Failed</h1>
      </div>

      <p>{{ $tr('destinationExplanation', { classroomName: selectedClassroomName }) }}</p>
      <p>{{ assignmentQuestion }}</p>
      <RecipientSelector
        v-if="current.matches('SELECT_GROUPS.SUCCESS')"
        v-model="selectedCollectionIds"
        :groups="context.groups"
        :classId="selectedClassroomId"
        :initialAdHocLearners="[]"
        data-test="recipient-selector"
        @updateLearners="learners => adHocLearners = learners"
      />
    </div>
  </KModal>

</template>


<script>

  import { createMachine, interpret, assign } from 'xstate';
  import sortBy from 'lodash/sortBy';
  import find from 'lodash/find';
  import { error as logError } from 'kolibri.lib.logging';
  import { LearnerGroupResource } from 'kolibri.resources';
  import commonCoreStrings from 'kolibri.coreVue.mixins.commonCoreStrings';
  import { coachStringsMixin } from '../../common/commonCoachStrings';
  import RecipientSelector from './RecipientSelector';

  const copyModalMachine = () =>
    createMachine({
      id: 'assignmentcopying',
      initial: 'SELECT_CLASSROOM',
      context: {
        groups: [],
      },
      states: {
        SELECT_CLASSROOM: {
          on: {
            fetchgroups: 'SELECT_GROUPS',
          },
        },
        SELECT_GROUPS: {
          // Event: { type: SELECT_GROUPS, classroomId }
          initial: 'GROUPS_LOADING',
          states: {
            GROUPS_LOADING: {
              invoke: {
                src(context, event) {
                  return LearnerGroupResource.fetchCollection({
                    getParams: { parent: event.classroomId },
                  });
                },
                onDone: {
                  target: 'GROUPS_OK',
                  actions: assign({ groups: (context, event) => event.data }),
                },
                onError: {
                  target: 'GROUPS_FAIL',
                },
              },
            },
            GROUPS_OK: {},
            GROUPS_FAIL: {},
          },
          on: {
            // TODO move Assignment API call here
            submit: 'SUCCESS',
          },
        },
        SUCCESS: {
          type: 'final',
        },
      },
    });

  export default {
    name: 'AssignmentCopyModal',
    components: {
      RecipientSelector,
    },
    mixins: [coachStringsMixin, commonCoreStrings],
    props: {
      modalTitle: {
        type: String,
        required: true,
      },
      assignmentQuestion: {
        type: String,
        required: true,
      },
      classId: {
        type: String,
        required: true,
      },
      classList: {
        type: Array,
        required: true,
      },
    },
    data() {
      return {
        // Machine
        machine: null,
        current: null,
        context: null,
        // Form state
        selectedClassroomId: null,
        selectedCollectionIds: [],
        adHocLearners: [],
      };
    },
    computed: {
      selectedClassroomName() {
        if (!this.selectedClassroomId) {
          return '';
        }
        return find(this.classList, { id: this.selectedClassroomId }).name;
      },
      atSelectClassroom() {
        return this.current.matches('SELECT_CLASSROOM');
      },
      blockControls() {
        return this.current.matches('SELECT_GROUPS.LOADING');
      },
      availableClassrooms() {
        // put current classroom on the top
        return sortBy(this.classList, classroom => (this.isCurrentClassroom(classroom) ? -1 : 1));
      },
      modalTexts() {
        if (this.atSelectClassroom) {
          return {
            submitText: this.coreString('continueAction'),
            cancelText: this.coreString('cancelAction'),
          };
        }
        return {
          submitText: this.coachString('copyAction'),
          cancelText: this.coreString('cancelAction'),
        };
      },
    },
    created() {
      this.selectedClassroomId = this.classId;
      // Start service on component creation
      this.setupMachine();
    },
    methods: {
      setupMachine() {
        this.machine = interpret(copyModalMachine());
        const { initialState, context } = this.machine;
        this.current = initialState;
        this.context = context;
        this.machine
          .onTransition(state => {
            this.current = state;
            this.context = state.context;
          })
          .onDone(() => this.emitSubmit())
          .start();
      },
      handleSubmit() {
        if (this.atSelectClassroom) {
          this.machine.send({ type: 'fetchgroups', classroomId: this.selectedClassroomId });
        } else {
          this.machine.send({ type: 'submit' });
        }
      },
      emitSubmit() {
        this.$emit(
          'submit',
          this.selectedClassroomId,
          this.selectedCollectionIds,
          this.adHocLearners
        );
      },
      classroomLabel(classroom) {
        if (this.isCurrentClassroom(classroom)) {
          return this.$tr('currentClass', { name: classroom.name });
        }
        return classroom.name;
      },
      isCurrentClassroom(classroom) {
        return classroom.id === this.classId;
      },
    },
    $trs: {
      currentClass: '{ name } (current class)',
      destinationExplanation: `Will be copied to '{classroomName}'`,
    },
  };

</script>


<style lang="scss" scoped></style>
