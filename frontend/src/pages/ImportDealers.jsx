import { useState } from 'react'
import {
  Box,
  Container,
  Heading,
  Text,
  SimpleGrid,
  Button,
  Card,
  CardBody,
  HStack,
  VStack,
  Badge,
  useToast,
  Icon,
  Divider,
} from '@chakra-ui/react'
import { useNavigate } from 'react-router-dom'
import { FaCheckCircle } from 'react-icons/fa'
import { dealersApi } from '../services/api'

const US_STATES = [
  { code: 'AL', name: 'Alabama' },
  { code: 'AK', name: 'Alaska' },
  { code: 'AZ', name: 'Arizona' },
  { code: 'AR', name: 'Arkansas' },
  { code: 'CA', name: 'California' },
  { code: 'CO', name: 'Colorado' },
  { code: 'CT', name: 'Connecticut' },
  { code: 'DE', name: 'Delaware' },
  { code: 'FL', name: 'Florida' },
  { code: 'GA', name: 'Georgia' },
  { code: 'HI', name: 'Hawaii' },
  { code: 'ID', name: 'Idaho' },
  { code: 'IL', name: 'Illinois' },
  { code: 'IN', name: 'Indiana' },
  { code: 'IA', name: 'Iowa' },
  { code: 'KS', name: 'Kansas' },
  { code: 'KY', name: 'Kentucky' },
  { code: 'LA', name: 'Louisiana' },
  { code: 'ME', name: 'Maine' },
  { code: 'MD', name: 'Maryland' },
  { code: 'MA', name: 'Massachusetts' },
  { code: 'MI', name: 'Michigan' },
  { code: 'MN', name: 'Minnesota' },
  { code: 'MS', name: 'Mississippi' },
  { code: 'MO', name: 'Missouri' },
  { code: 'MT', name: 'Montana' },
  { code: 'NE', name: 'Nebraska' },
  { code: 'NV', name: 'Nevada' },
  { code: 'NH', name: 'New Hampshire' },
  { code: 'NJ', name: 'New Jersey' },
  { code: 'NM', name: 'New Mexico' },
  { code: 'NY', name: 'New York' },
  { code: 'NC', name: 'North Carolina' },
  { code: 'ND', name: 'North Dakota' },
  { code: 'OH', name: 'Ohio' },
  { code: 'OK', name: 'Oklahoma' },
  { code: 'OR', name: 'Oregon' },
  { code: 'PA', name: 'Pennsylvania' },
  { code: 'RI', name: 'Rhode Island' },
  { code: 'SC', name: 'South Carolina' },
  { code: 'SD', name: 'South Dakota' },
  { code: 'TN', name: 'Tennessee' },
  { code: 'TX', name: 'Texas' },
  { code: 'UT', name: 'Utah' },
  { code: 'VT', name: 'Vermont' },
  { code: 'VA', name: 'Virginia' },
  { code: 'WA', name: 'Washington' },
  { code: 'WV', name: 'West Virginia' },
  { code: 'WI', name: 'Wisconsin' },
  { code: 'WY', name: 'Wyoming' },
]

export default function ImportDealers() {
  const [importing, setImporting] = useState({})
  const [imported, setImported] = useState({})
  const toast = useToast()
  const navigate = useNavigate()

  const handleImport = async (stateCode) => {
    setImporting(prev => ({ ...prev, [stateCode]: true }))
    try {
      await dealersApi.importFromState(stateCode)
      setImported(prev => ({ ...prev, [stateCode]: true }))
      toast({
        title: 'Import started',
        description: `Importing dealers from ${stateCode}. AI enrichment running in background.`,
        status: 'success',
        duration: 4000,
      })
    } catch (error) {
      console.error('Error importing:', error)
      toast({
        title: 'Import failed',
        description: error.message,
        status: 'error',
        duration: 3000,
      })
    } finally {
      setImporting(prev => ({ ...prev, [stateCode]: false }))
    }
  }

  return (
    <Container maxW="1400px" py={8}>
      <VStack align="stretch" spacing={6}>
        <Box>
          <HStack justify="space-between" mb={2}>
            <Heading size="lg">Import Dealers from ATF Database</Heading>
            <Button onClick={() => navigate('/dealers')} variant="ghost">
              ← Back to Dealers
            </Button>
          </HStack>
          <Text color="gray.600">
            Import Class 3 SOT dealer candidates from the official ATF FFL database. 
            The system will automatically verify Class 3 status via AI website analysis.
          </Text>
        </Box>

        <Card>
          <CardBody>
            <VStack align="stretch" spacing={4}>
              <Heading size="sm">How it works:</Heading>
              <HStack spacing={6}>
                <Box flex={1}>
                  <Text fontWeight="bold" fontSize="sm" mb={1}>1. Select State</Text>
                  <Text fontSize="sm" color="gray.600">Choose which state to import dealers from</Text>
                </Box>
                <Box flex={1}>
                  <Text fontWeight="bold" fontSize="sm" mb={1}>2. AI Enrichment</Text>
                  <Text fontSize="sm" color="gray.600">AI finds websites, contact info, verifies Class 3 status</Text>
                </Box>
                <Box flex={1}>
                  <Text fontWeight="bold" fontSize="sm" mb={1}>3. View Pipeline</Text>
                  <Text fontSize="sm" color="gray.600">Track dealers through discovery → enrichment → outreach</Text>
                </Box>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        <Divider />

        <Box>
          <Heading size="md" mb={4}>Select States to Import</Heading>
          <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={3}>
            {US_STATES.map((state) => (
              <Button
                key={state.code}
                size="md"
                variant={imported[state.code] ? 'solid' : 'outline'}
                colorScheme={imported[state.code] ? 'green' : 'brand'}
                isLoading={importing[state.code]}
                onClick={() => handleImport(state.code)}
                leftIcon={imported[state.code] ? <FaCheckCircle /> : undefined}
              >
                {state.code}
              </Button>
            ))}
          </SimpleGrid>
        </Box>
      </VStack>
    </Container>
  )
}
