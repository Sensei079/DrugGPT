import {
    Box,
    VStack,
    Text,
    Badge,
    Accordion,
    AccordionItem,
    AccordionButton,
    AccordionPanel,
    AccordionIcon,
    useColorModeValue,
} from '@chakra-ui/react';
import type { DrugResponse } from '../types/drug';

interface Props {
    results: DrugResponse;
}

function DrugResults({ results }: Props) {
    const bgColor = useColorModeValue('white', 'gray.700');
    const borderColor = useColorModeValue('gray.200', 'gray.600');

    const getResponseText = () => {
        const drugCount = results.drugs.length;
        if (drugCount === 0) return "No drugs found in your query.";
        if (drugCount === 1) {
            return `Here's what I found about ${results.drugs[0].name}:`;
        }
        return `I found information about ${drugCount} drugs:`;
    };

    return (
        <Box
            p={6}
            bg={bgColor}
            borderRadius="lg"
            boxShadow="md"
            borderWidth="1px"
            borderColor={borderColor}
        >
            <VStack spacing={4} align="stretch">
                <Text fontSize="lg" fontWeight="medium">
                    {getResponseText()}
                </Text>

                <Badge
                    colorScheme={results.safe ? 'green' : 'red'}
                    p={2}
                    borderRadius="md"
                    textAlign="center"
                    fontSize="md"
                >
                    {results.safe ? 'Safe to use together' : 'Potential interactions - Consult your doctor'}
                </Badge>

                <Accordion allowMultiple>
                    {results.drugs.map((drug, index) => (
                        <AccordionItem key={index}>
                            <AccordionButton>
                                <Box flex="1" textAlign="left" fontWeight="medium">
                                    {drug.name}
                                </Box>
                                <AccordionIcon />
                            </AccordionButton>
                            <AccordionPanel pb={4}>
                                <VStack align="stretch" spacing={3}>
                                    <Box>
                                        <Text fontWeight="medium" mb={1}>Description:</Text>
                                        <Text>{drug.info}</Text>
                                    </Box>
                                    <Box>
                                        <Text fontWeight="medium" mb={1}>Side Effects:</Text>
                                        <Text>{drug.side_effects}</Text>
                                    </Box>
                                    <Box>
                                        <Text fontWeight="medium" mb={1}>Warnings:</Text>
                                        <Text>{drug.warnings}</Text>
                                    </Box>
                                </VStack>
                            </AccordionPanel>
                        </AccordionItem>
                    ))}
                </Accordion>
            </VStack>
        </Box>
    );
}

export default DrugResults; 